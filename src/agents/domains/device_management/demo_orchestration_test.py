"""
EMS 设备管理 — 业务关联场景 (Orchestration) 验证脚本。
演示如何在一个 Action 成功后，由业务侧反馈并由 AI 引导后续的业务操作 (如: 设备配网)。
"""

import asyncio
import json
from src.agents.domains.device_management.tools.device_tools import (
    execute_business_action,
    get_interface_definition_schema
)

async def test_orchestration_flow():
    print(f"\n{'='*60}")
    print("🚀 [Step 1: 创建设备] 模拟录入一个新设备...")
    params = {
        "name": "BESS_AUTO_45",
        "device_type": "battery"
    }
    result_str = execute_business_action("create_device", params)
    result = json.loads(result_str)
    
    # 获取业务侧反馈的 ID 和后续动作
    device_id = result["result"]["id"]
    next_steps = result.get("orchestration_next_steps", [])
    
    print(f"业务响应: 设备录入成功ID: {device_id}")
    print(f"【关键】业务侧反馈的后续建议步数: {len(next_steps)}")
    
    if next_steps:
        next_action_info = next_steps[0]
        action_name = next_action_info["action"]
        reason = next_action_info["reason"]
        pre_filled = next_action_info["pre_filled_params"]
        
        print(f"\n🚀 [AI 引导逻辑]: 业务系统检测到你需要进行【{action_name}】。")
        print(f"原因: {reason}")
        print(f"预填入参数: {pre_filled}")
        
        # 模拟 AI 进一步查询下一步的参数定义
        print(f"\n🚀 [Step 2: 获取下一步 Schema] 加载 '{action_name}' 的规范...")
        next_schema_str = get_interface_definition_schema(action_name)
        next_schema = json.loads(next_schema_str)
        print(f"下一步所需要的全量参数: {list(next_schema['parameters']['properties'].keys())}")
        print(f"由于已预填 {list(pre_filled.keys())}，AI 只需要向用户追问: {set(next_schema['parameters']['required']) - set(pre_filled.keys())}")

    print(f"\n{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test_orchestration_flow())
