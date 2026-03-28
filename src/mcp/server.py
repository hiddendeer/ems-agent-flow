"""
EMS MCP 服务端基础实现。

本模块基于 fastmcp 框架，实现了“动态元数据”驱动的业务接口封装方案。
核心设计理念：
1. 大模型通过 list_entities 获取可以管理的业务类型。
2. 大模型通过 get_entity_fields 获取该类型的表单 Schema（JSON Schema）。
3. 大模型收集信息后，调用 save_entity 提交业务记录。

使用前请安装依赖：
pip install fastmcp
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 1. 初始化 MCP 服务器
mcp = FastMCP("EMS_Manager")

# 2. 单体后端配置：从环境变量获取 API 基准地址 (默认 localhost:8000)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

# 2. 定位 Schema 存储目录 (src/mcp/schemas)
BASE_DIR = Path(__file__).parent
SCHEMAS_DIR = BASE_DIR / "schemas"

def load_all_schemas() -> Dict[str, Dict[str, Any]]:
    """加载目录下所有的 JSON Schema"""
    schemas = {}
    if not SCHEMAS_DIR.exists():
        return schemas
        
    for p in SCHEMAS_DIR.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                name = data.get("entity_name", p.stem)
                schemas[name] = data
        except Exception as e:
            print(f"警告: 加载 Schema {p.name} 失败: {e}")
    return schemas

# --- 定义智能管理工具 (Tools) ---

@mcp.tool()
def list_manageable_entities() -> str:
    """列出系统中当前支持 AI 对话式新增/管理的业务实体类型。"""
    schemas = load_all_schemas()
    entities = [
        f"• {name}: {info.get('description', '无描述')}" 
        for name, info in schemas.items()
    ]
    if not entities:
        return "当前系统中尚未配置任何可管理的业务实体。"
    
    return "系统当前支持以下实体管理：\n" + "\n".join(entities)

@mcp.tool()
def get_entity_fields(entity_name: str) -> str:
    """
    根据实体名称，获取该实体的字段设计 Schema。
    大模型应以此引导用户填充或核对数据。
    """
    schemas = load_all_schemas()
    if entity_name not in schemas:
        return f"❌ 未找到名为 '{entity_name}' 的实体定义。"
    
    # 过滤掉内部路由配置，只给 LLM 看业务字段
    data = schemas[entity_name].copy()
    if "operations" in data:
        del data["operations"]
    
    return json.dumps(data, ensure_ascii=False, indent=2)

@mcp.tool()
def list_records(entity_name: str) -> str:
    """获取系统中已有的记录列表。"""
    schemas = load_all_schemas()
    config = schemas.get(entity_name, {}).get("operations", {}).get("list")
    if not config:
        return f"❌ 该实体不支持列表查询。"
    
    url = f"{API_BASE_URL}/{config['endpoint'].lstrip('/')}"
    # TODO: 执行 GET 请求
    return f"【正在从 {url} 获取 {entity_name} 列表...】\n• ID: 1, 名字: 1号电池组\n• ID: 2, 名字: 副产储能簇"

@mcp.tool()
def get_record_detail(entity_name: str, record_id: str) -> str:
    """根据 ID 获取某条记录的实时详细信息（用于编辑前的回显）。"""
    schemas = load_all_schemas()
    config = schemas.get(entity_name, {}).get("operations", {}).get("get")
    if not config:
        return f"❌ 该实体不支持详情查询。"
    
    endpoint = config['endpoint'].replace("{id}", record_id)
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    
    # 模拟返回该记录的当前值
    mock_data = {
        "device_name": "1号南侧电池组",
        "device_type": "BATTERY",
        "serial_number": "SN-M500",
        "capacity_kwh": 500
    }
    return json.dumps(mock_data, ensure_ascii=False, indent=2)

@mcp.tool()
def create_record(entity_name: str, record_data: Dict[str, Any]) -> str:
    """在系统中创建一条新的业务记录。"""
    schemas = load_all_schemas()
    config = schemas.get(entity_name, {}).get("operations", {}).get("create")
    if not config:
        return f"❌ 该实体不支持新建操作。"
    
    url = f"{API_BASE_URL}/{config['endpoint'].lstrip('/')}"
    print(f"--- POST {url} ---")
    return f"✅ 已成功录入【{entity_name}】数据。"

@mcp.tool()
def update_record(entity_name: str, record_id: str, updated_fields: Dict[str, Any]) -> str:
    """
    修改已有的业务记录。
    建议先通过 get_record_detail 获取详情，再引导用户提交需要修改的字段。
    """
    schemas = load_all_schemas()
    config = schemas.get(entity_name, {}).get("operations", {}).get("update")
    if not config:
        return f"❌ 该实体不支持更新操作。"
    
    endpoint = config['endpoint'].replace("{id}", record_id)
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    
    print(f"--- PUT {url} ---")
    print(f"修改内容: {json.dumps(updated_fields, ensure_ascii=False)}")
    return f"✅ 记录 {record_id} 更新成功！"

# --- 启动服务 ---
if __name__ == "__main__":
    # 使用 stdio 模式启动（适合作为本地 Agent 的子进程运行）
    mcp.run()
