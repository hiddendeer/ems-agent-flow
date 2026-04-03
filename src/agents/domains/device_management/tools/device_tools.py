"""
设备管理领域 Agent — 接口适配层。
将 agent 层与业务侧彻底解耦，通过读取 Schema 接口定义来动态引导对话和执行调用。
"""

from typing import Dict, Any, List, Optional
import json
from .schema_store import (
    fetch_all_interface_descriptions, 
    get_interface_schema, 
    simulate_business_logic_validation,
    get_business_next_steps
)

def list_business_interfaces() -> str:
    """列出可用业务接口清单"""
    interfaces = fetch_all_interface_descriptions()
    return "支持的业务操作：\n" + "\n".join([f"- {k}: {v}" for k, v in interfaces.items()])

def get_interface_definition_schema(action_name: str) -> str:
    """获取接口 JSON Schema"""
    schema = get_interface_schema(action_name)
    if not schema:
        return f"错误：未找到接口 '{action_name}'。"
    return json.dumps(schema, ensure_ascii=False, indent=2)

def execute_business_action(action_name: str, params: Dict[str, Any]) -> str:
    """
    业务执行网关。
    支持【业务串联编排】：响应结果中可能包含业务侧推荐的后续操作。
    """
    schema = get_interface_schema(action_name)
    if not schema:
        return f"接口不存在。"
    
    validation_result = simulate_business_logic_validation(action_name, params)
    
    if validation_result["status"] == "REJECTED":
        return json.dumps({
            "status": "ERROR",
            "message": validation_result["message"]
        }, ensure_ascii=False, indent=2)
    
    # 模拟生成的业务 ID
    business_id = f"DEV_{params.get('name', 'ID').upper()}_001"
    
    # 最终业务成功响应
    response = {
        "status": "SUCCESS",
        "action": action_name,
        "message": f"'{action_name}' 成功完成。",
        "result": {
            "id": business_id,
            "data": params
        },
        # 【业务关联扩展】：反馈业务建议的下一个动作
        "orchestration_next_steps": get_business_next_steps(action_name, {"id": business_id})
    }
    
    return json.dumps(response, ensure_ascii=False, indent=2)
