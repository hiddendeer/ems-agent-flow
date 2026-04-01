"""
EMS 设备管理 — 业务-AI 融合逻辑验证脚本。
演示如何通过动态 Schema 驱动对话流程并处理业务冲突。
"""

import asyncio
import json
from src.agents.domains.device_management.tools.device_tools import (
    list_business_interfaces,
    get_interface_definition_schema,
    execute_business_action
)

async def test_business_fusion_flow():
    print(f"\n{'='*60}")
    print("🚀 [Step 1: 接口发现] 查找当前业务支持的操作...")
    interfaces = list_business_interfaces()
    print(interfaces)
    
    action = "create_device"
    print(f"\n🚀 [Step 2: 参数推导] 获取 '{action}' 的业务入参规范...")
    schema_str = get_interface_definition_schema(action)
    schema = json.loads(schema_str)
    print(f"该操作需要参数: {list(schema['parameters']['properties'].keys())}")
    print(f"其中必填项为: {schema['parameters']['required']}")
    
    # 模拟一个会触发业务冲突的参数 (名称重复)
    print(f"\n🚀 [Step 3: 模拟调用 - 触发业务录入失败]")
    params_conflict = {
        "name": "BESS_01",  # 这是一个已存在的名称
        "device_type": "battery",
        "capacity_kwh": 250.0
    }
    print(f"尝试录入重复名称的设备: {params_conflict['name']}...")
    result_conflict = execute_business_action(action, params_conflict)
    print(f"业务系统反馈: {result_conflict}")
    
    # 模拟一个数值超限的参数
    print(f"\n🚀 [Step 4: 模拟调用 - 触发容量数值超限]")
    params_invalid = {
        "name": "BESS_NEW_02",
        "device_type": "battery",
        "capacity_kwh": 9999.9  # 超过了 Schema 定义的 5000
    }
    result_invalid = execute_business_action(action, params_invalid)
    print(f"业务系统反馈: {result_invalid}")
    
    # 模拟一个正常的调用
    print(f"\n🚀 [Step 5: 最终录入 - 合法数据]")
    params_ok = {
        "name": "BESS_SUCCESS_05",
        "device_type": "battery",
        "capacity_kwh": 1500.0,
        "location": "A区3号位"
    }
    result_ok = execute_business_action(action, params_ok)
    print(f"业务系统成功反馈: {result_ok}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test_business_fusion_flow())
