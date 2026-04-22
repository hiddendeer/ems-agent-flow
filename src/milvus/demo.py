import hashlib
import json
import logging
import os
import threading
import uuid
from typing import Optional
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
from llama_index.core.schema import TextNode
from llama_index.vector_stores.milvus import MilvusVectorStore
from langchain_openai import OpenAIEmbeddings as LangchainOpenAIEmbeddings
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
import jieba


# 1. 智谱向量化方案赋给 LlamaIndex 全局 Settings
_openai_api_key = os.getenv("OPENAI_API_KEY")
if not _openai_api_key:
    raise RuntimeError("环境变量 OPENAI_API_KEY 未配置，服务无法启动")

lc_embed_model = LangchainOpenAIEmbeddings(
    model="embedding-3",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4",
    openai_api_key=_openai_api_key
)
Settings.embed_model = LangchainEmbedding(lc_embed_model)
Settings.llm = None

# 2. LlamaIndex 原生分块器
splitter = SentenceSplitter(chunk_size=600, chunk_overlap=60)
Settings.node_parser = splitter

# 3. 初始化 Milvus VectorStore
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

storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

# ==========================================
# 混合检索：本地 Node 缓存逻辑
# ==========================================
NODES_CACHE_PATH = "temp_uploads/nodes_cache.json"
DOC_HASHES_PATH = "temp_uploads/doc_hashes.json"

_nodes_lock = threading.Lock()
all_nodes: list = []
_doc_hashes: set = set()
_bm25_retriever: Optional[BM25Retriever] = None
_bm25_dirty = True


def _sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename)
    return name.replace("\x00", "") or "unknown"


def save_nodes():
    os.makedirs("temp_uploads", exist_ok=True)
    try:
        data = [node.to_dict() for node in all_nodes]
        with open(NODES_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info("Nodes cache saved. Total: %d", len(all_nodes))
    except Exception as e:
        logger.error("Failed to save nodes cache: %s", e)


def load_nodes():
    global all_nodes, _doc_hashes
    if os.path.exists(NODES_CACHE_PATH):
        try:
            with open(NODES_CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_nodes = [TextNode.from_dict(d) for d in data]
            logger.info("Nodes cache loaded. Total: %d", len(all_nodes))
        except Exception as e:
            logger.error("Failed to load nodes cache: %s", e)
    if os.path.exists(DOC_HASHES_PATH):
        try:
            with open(DOC_HASHES_PATH, "r", encoding="utf-8") as f:
                _doc_hashes = set(json.load(f))
        except Exception as e:
            logger.error("Failed to load doc hashes: %s", e)


def save_doc_hashes():
    try:
        with open(DOC_HASHES_PATH, "w", encoding="utf-8") as f:
            json.dump(list(_doc_hashes), f)
    except Exception as e:
        logger.error("Failed to save doc hashes: %s", e)


def _get_bm25_retriever() -> Optional[BM25Retriever]:
    global _bm25_retriever, _bm25_dirty
    with _nodes_lock:
        if not all_nodes:
            return None
        if _bm25_dirty or _bm25_retriever is None:
            _bm25_retriever = BM25Retriever.from_defaults(
                nodes=list(all_nodes),
                similarity_top_k=50,
                tokenizer=chinese_tokenizer
            )
            _bm25_dirty = False
        return _bm25_retriever


def chinese_tokenizer(text: str):
    return list(jieba.cut(text))


load_nodes()
# ==========================================

app = FastAPI(title="LlamaIndex Powered Milvus API")
md = MarkItDown()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
_READ_CHUNK = 64 * 1024           # 64KB

# ==========================================
# FastAPI 接口定义
# ==========================================
@app.post("/convert", summary="LlamaIndex 文件处理入库")
def process_file_with_llama_index(file: UploadFile = File(...)):
    global _bm25_dirty

    safe_name = _sanitize_filename(file.filename or "unknown")
    allowed_extensions = {".docx", ".pptx", ".pdf", ".xlsx", ".zip"}
    _, ext = os.path.splitext(safe_name)
    if ext.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

    os.makedirs("temp_uploads", exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    temp_path = os.path.join("temp_uploads", unique_name)

    try:
        # 流式读取，边读边检查大小上限
        chunks = []
        total = 0
        while True:
            chunk = file.file.read(_READ_CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="文件大小超过 50MB 限制")
            chunks.append(chunk)
        content = b"".join(chunks)

        # 文档去重：基于内容 SHA-256
        content_hash = hashlib.sha256(content).hexdigest()
        with _nodes_lock:
            if content_hash in _doc_hashes:
                return {
                    "filename": safe_name,
                    "doc_id": None,
                    "status": "skipped",
                    "message": "文档内容已存在，跳过重复入库"
                }

        with open(temp_path, "wb") as buffer:
            buffer.write(content)

        logger.info("[%s] Extracting Text with MarkItDown...", safe_name)
        result = md.convert(temp_path)
        full_text = result.text_content

        if not full_text:
            raise HTTPException(status_code=400, detail="文档无内容")

        doc_id = str(uuid.uuid4())
        llama_doc = Document(
            text=full_text,
            doc_id=doc_id,
            metadata={"source": safe_name}
        )

        logger.info("[%s] Pushing into LlamaIndex Vector Queue...", safe_name)
        index.insert(llama_doc)

        doc_nodes = Settings.node_parser.get_nodes_from_documents([llama_doc])

        with _nodes_lock:
            all_nodes.extend(doc_nodes)
            _doc_hashes.add(content_hash)
            _bm25_dirty = True
            save_nodes()
            save_doc_hashes()

        return {
            "filename": safe_name,
            "doc_id": doc_id,
            "status": "success",
            "message": "已成功被 LlamaIndex 处理并写入 Milvus!"
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to process file %s", safe_name)
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
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    try:
        logger.info("[Query] %s", request.query)

        vector_retriever = index.as_retriever(similarity_top_k=request.limit)
        bm25 = _get_bm25_retriever()

        if bm25 is None:
            logger.info("BM25 nodes cache is empty, using vector search only.")
            retrieved_nodes = vector_retriever.retrieve(request.query)
        else:
            fusion_retriever = QueryFusionRetriever(
                [vector_retriever, bm25],
                similarity_top_k=request.limit,
                num_queries=1,
                mode="reciprocal_rerank",
                use_async=False
            )
            retrieved_nodes = fusion_retriever.retrieve(request.query)

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
