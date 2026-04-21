import time
import random
from pymilvus import FieldSchema, CollectionSchema, DataType, Collection, utility

try:
    from .client import milvus_manager
except ImportError:
    from client import milvus_manager

def setup_enterprise_rag_collection():
    print("Testing Milvus connection...")
    try:
        milvus_manager.connect()
    except Exception as e:
        print(f"Connection failed: {e}")
        return
        
    if not milvus_manager.is_connected():
        print("Milvus not connected. Aborting.")
        return

    collection_name = "enterprise_knowledge"
    dim = 128  # 演示用维度。实际应替换为你的 embedding 模型对应的维度 (如 768, 1024, 1536)

    # 如果存在旧表，在演示中先删掉以便重新创建
    if utility.has_collection(collection_name):
        print(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name)
    
    # ---------------- 1. 设计 Schema ----------------
    print(f"1. Creating schema for {collection_name}...")
    
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True, description="唯一主键"),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim, description="文本向量"),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=4096, description="文本块内容"),
        FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=128, description="原始文档编号"),
        FieldSchema(name="doc_title", dtype=DataType.VARCHAR, max_length=256, description="原始文档名称"),
        FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=64, description="文档类型"),
        FieldSchema(name="department", dtype=DataType.VARCHAR, max_length=64, description="可见部门"),
        FieldSchema(name="chunk_index", dtype=DataType.INT32, description="块的段落索引"),
        FieldSchema(name="created_at", dtype=DataType.INT64, description="入库时间戳")
    ]
    
    schema = CollectionSchema(fields=fields, description="企业级 RAG 知识库集合")
    collection = Collection(name=collection_name, schema=schema)
    
    # ---------------- 2. 插入测试数据 ----------------
    print("2. Generating and inserting mock data...")
    num_entities = 5
    current_time = int(time.time())
    
    # 模拟两类不同的公司文档
    mock_data = [
        # doc 1: 销售案例
        {
            "text": "客户投诉产品 A 不兼容旧系统，我们通过提供兼容补丁模块成功解决，未发生退货。",
            "doc_id": "doc_case_001", "title": "2023年第一季度退货挽回案例",
            "type": "销售案例", "dept": "销售部", "idx": 0
        },
        {
            "text": "最终复盘：销售应在此类老客户报价时，直接捆绑基础适配服务包。",
            "doc_id": "doc_case_001", "title": "2023年第一季度退货挽回案例",
            "type": "销售案例", "dept": "销售部", "idx": 1
        },
        # doc 2: 研发规范
        {
            "text": "所有对外暴露的 API 接口，必须严格执行 JWT 鉴权验证，密码传输使用 RSA+AES 混合加密方案。",
            "doc_id": "doc_tech_099", "title": "公司后端安全开发红线规范",
            "type": "技术规范", "dept": "研发部", "idx": 0
        },
        # doc 3: 人事通知
        {
            "text": "即日起，每月 15 号前需在系统内完成本月绩效考核 KPI 的自我评定。",
            "doc_id": "doc_hr_021", "title": "关于调整绩效考核填写周期的通知",
            "type": "行政通知", "dept": "全员", "idx": 0
        },
        {
            "text": "一旦逾期未填，绩效成绩默认按 C 档（合格处理），由于个人原因导致漏填不接受补填申请。",
            "doc_id": "doc_hr_021", "title": "关于调整绩效考核填写周期的通知",
            "type": "行政通知", "dept": "全员", "idx": 1
        }
    ]

    # 按表头顺序分别构建列数据
    embeddings = [[random.random() for _ in range(dim)] for _ in range(num_entities)]
    chunk_texts = [d["text"] for d in mock_data]
    doc_ids = [d["doc_id"] for d in mock_data]
    doc_titles = [d["title"] for d in mock_data]
    doc_types = [d["type"] for d in mock_data]
    departments = [d["dept"] for d in mock_data]
    chunk_indexes = [d["idx"] for d in mock_data]
    created_ats = [current_time] * num_entities

    insert_result = collection.insert([
        embeddings, chunk_texts, doc_ids, doc_titles, 
        doc_types, departments, chunk_indexes, created_ats
    ])
    print(f"Inserted {insert_result.insert_count} entities.")
    
    # ---------------- 3. 创建索引并加载进内存 ----------------
    print("3. Creating vector index...")
    # 对向量字段建索引
    index_params = {
        "metric_type": "L2",       # 或者 "IP", "COSINE" (依赖于你的 Embedding)
        "index_type": "IVF_FLAT",  # 最常用的量化索引
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    
    # 对高频过滤的标量字段建索引(大幅提升混合检索性能)
    collection.create_index(field_name="doc_type")
    collection.create_index(field_name="department")
    
    print("Loading collection to memory...")
    collection.load()
    
    # ---------------- 4. 模拟包含过滤条件的搜索 ----------------
    print("\n4. Performing Hybrid Search (Vector search + Filter)...")
    
    # 模拟用户提问生成的向量
    search_vec = [[random.random() for _ in range(dim)]]
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
    
    # 场景演示：用户是销售，搜索如何处理退货，系统过滤出只属于 "销售部"或"全员" 的案例类型
    filter_expr = "department in ['销售部', '全员'] and doc_type == '销售案例'"
    
    results = collection.search(
        data=search_vec, 
        anns_field="embedding", 
        param=search_params,
        limit=2,
        expr=filter_expr,  # 这是关键，标量过滤条件
        output_fields=["chunk_text", "doc_title", "doc_type", "department"] # 我们需要展示给用户的元数据
    )
    
    print(f"\n--- Search Filtered by: {filter_expr} ---")
    for hits in results:
        for hit in hits:
            print("-" * 40)
            print(f"距离 (Distance): {hit.distance:.4f}")
            print(f"来源 (Source): {hit.entity.get('doc_title')} | 归属: {hit.entity.get('department')}")
            print(f"内容 (Content): {hit.entity.get('chunk_text')}")
    
    milvus_manager.disconnect()
    
if __name__ == "__main__":
    setup_enterprise_rag_collection()
