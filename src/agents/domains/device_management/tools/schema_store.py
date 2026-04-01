"""
模拟业务系统的 Schema 服务中心。
"""

from typing import Dict, Any

# 模拟业务侧维护的接口元数据
BUSINESS_SCHEMA_STORE = {
    "create_device": {
        "id": "api_v1_device_create",
        "name": "创建设备",
        "description": "录入并初始化一个新的能源管理设备",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "设备的可读名称", "required": True},
                "device_type": {"type": "string", "description": "设备类别", "required": True, "enum": ["battery", "inverter", "meter"]}
            },
            "required": ["name", "device_type"]
        }
    },
    "configure_network": {
        "id": "api_v1_device_network_config",
        "name": "设备配网",
        "description": "为新录入的设备配置 IP、网关、端口等通信参数",
        "parameters": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "设备 ID", "required": True},
                "ip_address": {"type": "string", "description": "设备静态 IP 地址", "required": True},
                "protocol": {"type": "string", "description": "通信协议 (ModbusTCP / MQTT)", "required": True}
            },
            "required": ["device_id", "ip_address", "protocol"]
        }
    }
}

# 模拟已存在的业务数据
EXISTING_DEVICE_NAMES = ["BESS_01"]

def fetch_all_interface_descriptions() -> Dict[str, str]:
    return {k: v["description"] for k, v in BUSINESS_SCHEMA_STORE.items()}

def get_interface_schema(action_name: str) -> Dict[str, Any]:
    return BUSINESS_SCHEMA_STORE.get(action_name, {})

def simulate_business_logic_validation(action_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if action_name == "create_device":
        name = params.get("name")
        if name in EXISTING_DEVICE_NAMES:
            return {
                "status": "REJECTED",
                "message": f"设备名称 '{name}' 已存在。"
            }
            
    return {"status": "SUCCESS", "message": "校验通过。"}

def get_business_next_steps(action_name: str, result_data: Dict[str, Any]) -> list:
    """
    业务逻辑编排：根据当前动作的结果，反馈后续建议执行的业务动作。
    这是业务侧驱动的编排逻辑，Agent 只负责读取并展示。
    """
    if action_name == "create_device":
        # 如果创建成功，业务系统建议下一步进行 "设备配网"
        return [
            {
                "action": "configure_network",
                "reason": "新录入的设备需要完成网络初始化才能上线。",
                "pre_filled_params": {
                    "device_id": result_data.get("id", "UNKNOWN_ID")
                }
            }
        ]
    return []
