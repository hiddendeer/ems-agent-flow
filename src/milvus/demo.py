import hashlib
import json
import logging
import os
import threading
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from markitdown import MarkItDown
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("milvus_demo")

# ==========================================
# LlamaIndex 库依赖导入
# ==========================================
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import TextNode
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.milvus import MilvusVectorStore
from langchain_openai import OpenAIEmbeddings as LangchainOpenAIEmbeddings
import jieba

# ==========================================
# 配置与初始化
# ==========================================
_openai_api_key = os.getenv("OPENAI_API_KEY")
if not _openai_api_key:
    raise RuntimeError("环境变量 OPENAI_API_KEY 未配置，服务无法启动")

lc_embed_model = LangchainOpenAIEmbeddings(
    model="embedding-3",
    openai_api_base="https://open.bigmodel.cn/api/paas/v4",
    openai_api_key=_openai_api_key,
)
Settings.embed_model = LangchainEmbedding(lc_embed_model)
Settings.llm = None

splitter = SentenceSplitter(chunk_size=600, chunk_overlap=60)
Settings.node_parser = splitter

_milvus_host = (
    os.getenv("MILVUS_HOST", "localhost")
    .replace("http://", "")
    .replace("https://", "")
    .strip("/")
)
_milvus_port = os.getenv("MILVUS_PORT", "19530")
_milvus_uri = f"http://{_milvus_host}:{_milvus_port}"
_milvus_user = os.getenv("MILVUS_USER", "root")
_milvus_password = os.getenv("MILVUS_PASSWORD", "")
_milvus_token = f"{_milvus_user}:{_milvus_password}" if _milvus_password else ""

COLLECTION_NAME = "llama_markdown_collection"
TEMP_DIR = Path("temp_uploads")
NODES_CACHE_PATH = TEMP_DIR / "nodes_cache.json"
DOC_HASHES_PATH = TEMP_DIR / "doc_hashes.json"
MAX_FILE_SIZE = 50 * 1024 * 1024
_READ_CHUNK = 64 * 1024

vector_store = MilvusVectorStore(
    uri=_milvus_uri,
    token=_milvus_token,
    collection_name=COLLECTION_NAME,
    dim=2048,
    overwrite=False,
)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)

# ==========================================
# 混合检索：本地 Node 缓存
# ==========================================
_nodes_lock = threading.Lock()
all_nodes: list = []
_doc_hashes: set = set()
_pending_hashes: set = set()  # 处理中的文档哈希，防止并发重复入库
_bm25_retriever: Optional[BM25Retriever] = None
_bm25_dirty = True


def chinese_tokenizer(text: str) -> list:
    return list(jieba.cut(text))


def _sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename)
    return name.replace("\x00", "") or "unknown"


def save_nodes(nodes_snapshot: list) -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        data = [node.to_dict() for node in nodes_snapshot]
        with open(NODES_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        logger.info("Nodes cache saved. Total: %d", len(nodes_snapshot))
    except Exception as e:
        logger.error("Failed to save nodes cache: %s", e)


def save_doc_hashes(hashes_snapshot: set) -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(DOC_HASHES_PATH, "w", encoding="utf-8") as f:
            json.dump(list(hashes_snapshot), f)
    except Exception as e:
        logger.error("Failed to save doc hashes: %s", e)


def load_nodes() -> None:
    global all_nodes, _doc_hashes
    if NODES_CACHE_PATH.exists():
        try:
            with open(NODES_CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            all_nodes = [TextNode.from_dict(d) for d in data]
            logger.info("Nodes cache loaded. Total: %d", len(all_nodes))
        except Exception as e:
            logger.error("Failed to load nodes cache: %s", e)
    if DOC_HASHES_PATH.exists():
        try:
            with open(DOC_HASHES_PATH, "r", encoding="utf-8") as f:
                _doc_hashes = set(json.load(f))
        except Exception as e:
            logger.error("Failed to load doc hashes: %s", e)


def _get_bm25_retriever() -> Optional[BM25Retriever]:
    global _bm25_retriever, _bm25_dirty
    with _nodes_lock:
        if not all_nodes:
            return None
        if _bm25_dirty or _bm25_retriever is None:
            _bm25_retriever = BM25Retriever.from_defaults(
                nodes=list(all_nodes),
                similarity_top_k=50,
                tokenizer=chinese_tokenizer,
            )
            _bm25_dirty = False
        return _bm25_retriever


# ==========================================
# FastAPI App
# ==========================================
@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_nodes()
    yield


app = FastAPI(title="LlamaIndex Powered Milvus API", lifespan=lifespan)
md = MarkItDown()


@app.post("/convert", summary="LlamaIndex 文件处理入库")
def process_file_with_llama_index(file: UploadFile = File(...)):
    global _bm25_dirty, all_nodes, _doc_hashes

    safe_name = _sanitize_filename(file.filename or "unknown")
    _, ext = os.path.splitext(safe_name)
    if ext.lower() not in {".docx", ".pptx", ".pdf", ".xlsx", ".zip"}:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}_{safe_name}"
    _hash_registered = False
    content_hash = ""

    try:
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

        content_hash = hashlib.sha256(content).hexdigest()
        with _nodes_lock:
            if content_hash in _doc_hashes or content_hash in _pending_hashes:
                return {
                    "filename": safe_name,
                    "doc_id": None,
                    "status": "skipped",
                    "message": "文档内容已存在，跳过重复入库",
                }
            _pending_hashes.add(content_hash)
        _hash_registered = True

        temp_path.write_bytes(content)

        logger.info("[%s] Extracting text with MarkItDown...", safe_name)
        result = md.convert(str(temp_path))
        full_text = (result.text_content or "").strip()
        if not full_text:
            raise HTTPException(status_code=400, detail="文档无内容")

        doc_id = str(uuid.uuid4())
        llama_doc = Document(
            text=full_text,
            doc_id=doc_id,
            metadata={"source": safe_name},
        )

        logger.info("[%s] Inserting into Milvus via LlamaIndex...", safe_name)
        index.insert(llama_doc)

        doc_nodes = Settings.node_parser.get_nodes_from_documents([llama_doc])

        with _nodes_lock:
            all_nodes = [*all_nodes, *doc_nodes]
            _doc_hashes = _doc_hashes | {content_hash}
            _pending_hashes.discard(content_hash)
            _bm25_dirty = True
            nodes_snapshot = list(all_nodes)
            hashes_snapshot = set(_doc_hashes)

        save_nodes(nodes_snapshot)
        save_doc_hashes(hashes_snapshot)

        return {
            "filename": safe_name,
            "doc_id": doc_id,
            "status": "success",
            "message": "已成功被 LlamaIndex 处理并写入 Milvus!",
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to process file %s", safe_name)
        raise HTTPException(status_code=500, detail="文件处理失败，请稍后重试")
    finally:
        if _hash_registered:
            with _nodes_lock:
                _pending_hashes.discard(content_hash)
        if temp_path.exists():
            temp_path.unlink()


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=50)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)


@app.post("/search", summary="LlamaIndex 原生语义检索")
def llama_search(request: SearchRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="查询内容不能为空")

    try:
        logger.info("[Query] %s", query)

        vector_retriever = index.as_retriever(similarity_top_k=request.limit)
        bm25 = _get_bm25_retriever()

        if bm25 is None:
            logger.info("BM25 nodes cache is empty, using vector search only.")
            retrieved_nodes = vector_retriever.retrieve(query)
        else:
            fusion_retriever = QueryFusionRetriever(
                [vector_retriever, bm25],
                similarity_top_k=request.limit,
                num_queries=1,
                mode="reciprocal_rerank",
                use_async=False,
            )
            retrieved_nodes = fusion_retriever.retrieve(query)

        results = []
        for node in retrieved_nodes:
            score = round(node.score, 4) if node.score is not None else 0.0
            if score >= request.min_score:
                results.append({
                    "score": score,
                    "doc_source": node.metadata.get("source", "Unknown"),
                    "chunk_text": node.text,
                })

        return {
            "query": query,
            "results_count": len(results),
            "results": results,
        }
    except Exception:
        logger.exception("Search failed for query: %s", query)
        raise HTTPException(status_code=500, detail="检索失败，请稍后重试")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.milvus.demo:app", host="0.0.0.0", port=8001, reload=True)
