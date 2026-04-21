import logging
import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from markitdown import MarkItDown

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger("milvus_demo")
logging.basicConfig(level=logging.INFO)

# ==========================================
# LlamaIndex 库依赖导入
# ==========================================
from llama_index.core import Settings, Document, VectorStoreIndex, StorageContext
from llama_index.vector_stores.milvus import MilvusVectorStore
from langchain_openai import OpenAIEmbeddings as LangchainOpenAIEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.core.node_parser import SentenceSplitter

# 1. 调整配置：将智谱的大模型向量化方案赋给 LlamaIndex 全局 Settings
_openai_api_key = os.getenv("OPENAI_API_KEY")
if not _openai_api_key:
    raise RuntimeError("环境变量 OPENAI_API_KEY 未配置，服务无法启动")

lc_embed_model = LangchainOpenAIEmbeddings(
    model="embedding-3",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4",
    openai_api_key=_openai_api_key
)
Settings.embed_model = LangchainEmbedding(lc_embed_model)

# 我们只用来做索引和检索，不需要生成答案，关闭大语言模型调用
Settings.llm = None

# 2. 将之前基于 Langchain 的 Splitter 换成 LlamaIndex 的原生分块器 (SentenceSplitter)
splitter = SentenceSplitter(chunk_size=600, chunk_overlap=60)
Settings.node_parser = splitter

# 3. 初始化原生 LlamaIndex 的 Milvus VectorStore
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_host = milvus_host.replace("http://", "").replace("https://", "").strip("/")
milvus_port = os.getenv("MILVUS_PORT", "19530")
milvus_uri = f"http://{milvus_host}:{milvus_port}"

milvus_user = os.getenv("MILVUS_USER", "root")
milvus_password = os.getenv("MILVUS_PASSWORD", "")
milvus_token = f"{milvus_user}:{milvus_password}" if milvus_password else ""

COLLECTION_NAME = "llama_markdown_collection"
vector_store = MilvusVectorStore(
    uri=milvus_uri,
    token=milvus_token,
    collection_name=COLLECTION_NAME,
    dim=2048,
    overwrite=False
)

# 根据 VectorStore 和 StorageContext 构建核心检索和插入引擎
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

# 初始化应用
app = FastAPI(title="LlamaIndex Powered Milvus API")
md = MarkItDown()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# ==========================================
# FastAPI 接口定义
# ==========================================
@app.post("/convert", summary="LlamaIndex 文件处理入库")
def process_file_with_llama_index(file: UploadFile = File(...)):
    """
    使用 LlamaIndex 原生方案：
    文件转 Markdown -> 一键封装为 Document -> Insert 进索引
    LlamaIndex 会全自动将 Document 切分 (Node) 并发给智谱转 Embedding 写入 Milvus。
    """
    allowed_extensions = {".docx", ".pptx", ".pdf", ".xlsx", ".zip"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

    os.makedirs("temp_uploads", exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    temp_path = os.path.join("temp_uploads", unique_name)

    try:
        content = file.file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超过 50MB 限制")
        with open(temp_path, "wb") as buffer:
            buffer.write(content)

        logger.info("[%s] Extracting Text with MarkItDown...", file.filename)
        result = md.convert(temp_path)
        full_text = result.text_content

        if not full_text:
            raise HTTPException(status_code=400, detail="文档无内容")

        # 将长文本封装为一个 LlamaIndex Document 对象
        # 将原文件名作为 MetaData 传入，LlamaIndex 会自己继承到后续碎片中
        doc_id = str(uuid.uuid4())
        llama_doc = Document(
            text=full_text,
            doc_id=doc_id,
            metadata={"source": file.filename}
        )

        logger.info("[%s] Pushing into LlamaIndex Vector Queue...", file.filename)

        # 仅仅调用一句 insert，LlamaIndex 将大包大揽为您完成下面任务：
        # 1. 经过 Settings.node_parser 切分成 Node（文本块）
        # 2. 依次发给智谱 API 换取 Embedding 向量
        # 3. 带上元数据将文本和向量插入到真实的 Milvus 库中
        index.insert(llama_doc)

        return {
            "filename": file.filename,
            "doc_id": doc_id,
            "status": "success",
            "message": "已成功被 LlamaIndex 处理并写入 Milvus!"
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to process file %s", file.filename)
        raise HTTPException(status_code=500, detail="文件处理失败，请稍后重试")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

            
class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)

@app.post("/search", summary="LlamaIndex 原生语义检索")
def llama_search(request: SearchRequest):
    """
    高度封装好的 LlamaIndex 检索系统！
    只需要提供 Query 对象即可自动完成：文本转 Embeddings -> 发令 Milvus 查找近似度 -> 组结果。
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    try:
        logger.info("[Query] %s", request.query)

        retriever = index.as_retriever(similarity_top_k=request.limit)

        # retrieve 就是一切！自动调用了智谱的转化和 Milvus 的检索算法
        retrieved_nodes = retriever.retrieve(request.query)

        formatted_results = []
        for node in retrieved_nodes:
            score = round(node.score, 4) if node.score else 0.0
            if score < request.min_score:
                continue
            formatted_results.append({
                "score": score,
                "doc_source": node.metadata.get("source", "Unknown"),
                "chunk_text": node.text,
            })

        return {
            "query": request.query,
            "results_count": len(formatted_results),
            "results": formatted_results
        }
    except Exception:
        logger.exception("Search failed for query: %s", request.query)
        raise HTTPException(status_code=500, detail="检索失败，请稍后重试")


if __name__ == "__main__":
    import uvicorn
    print("Starting LlamaIndex Powered FastAPI server on http://0.0.0.0:8001")
    uvicorn.run("src.milvus.demo:app", host="0.0.0.0", port=8001, reload=True)
