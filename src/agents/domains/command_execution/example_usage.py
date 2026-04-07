"""
执行提案使用示例

展示如何在业务层使用 Agent 返回的结构化执行提案。
"""

import json
from typing import Dict, Any

from schemas import ExecutionProposal, ProposalResponse, ProposalStatus
from tools.generate_proposal import (
    parse_proposal_from_json,
    validate_proposal_signature
)


# ========================================================================
# 场景 1: Agent 生成执行提案
# ========================================================================

def agent_generates_proposal() -> str:
    """
    Agent 审查指令后，调用 generate_execution_proposal 工具生成提案
    """
    # 这是 Agent 会调用的工具
    proposal_json = generate_execution_proposal(
        command_type="charge",
        device_id="dev_001",
        device_type="PCS",
        parameters={
            "power": 100.0,
            "target_soc": 80
        },
        api_endpoint="/api/v1/devices/pcs/charge",
        http_method="POST",
        validation_passed=True,
        validation_details={
            "parameter_validation": True,
            "safety_check": True,
            "permission_check": True
        },
        risk_level="low",
        risk_factors=[],
        confidence_score=0.95,
        review_summary="指令通过安全审查。功率100kW在安全范围内，目标SOC 80%合理。设备状态正常，建议执行。",
        operator="system",
        session_id="sess_20260403_001",
        priority=5,
        timeout_seconds=30,
        retry_count=3
    )

    return proposal_json


# ========================================================================
# 场景 2: 业务 API 接收并执行提案
# ========================================================================

class DeviceAPIClient:
    """设备 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def execute_proposal(self, proposal_json: str) -> Dict[str, Any]:
        """
        执行 Agent 返回的提案

        Args:
            proposal_json: Agent 返回的 JSON 格式提案

        Returns:
            执行结果
        """
        # 1. 解析提案
        response = parse_proposal_from_json(proposal_json)

        if not response.success:
            return {
                "success": False,
                "error": response.error,
                "message": response.message
            }

        proposal = response.proposal

        # 2. 验证提案签名（防止伪造）
        if not validate_proposal_signature(proposal):
            return {
                "success": False,
                "error": "Invalid proposal signature"
            }

        # 3. 检查是否安全可执行
        if not proposal.is_safe_to_execute():
            return {
                "success": False,
                "error": "Proposal is not safe to execute",
                "status": proposal.status,
                "risk_level": proposal.risk_assessment.risk_level
            }

        # 4. 转换为执行请求
        execution_request = proposal.to_execution_request()

        # 5. 调用实际的设备 API
        try:
            result = await self._call_device_api(execution_request)

            # 6. 返回执行结果
            return {
                "success": True,
                "proposal_id": proposal.proposal_id,
                "execution_result": result,
                "executed_at": result.get("executed_at")
            }

        except Exception as e:
            return {
                "success": False,
                "proposal_id": proposal.proposal_id,
                "error": str(e),
                "message": "Execution failed"
            }

    async def _call_device_api(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用实际的设备 API

        Args:
            request: 执行请求字典

        Returns:
            API 响应
        """
        # 这里实现实际的 API 调用逻辑
        # 例如：使用 httpx 或 aiohttp 发送 HTTP 请求

        api_endpoint = request["api_endpoint"]
        http_method = request["http_method"]
        parameters = request["parameters"]
        device_id = request["device_id"]

        # 模拟 API 调用
        print(f"📡 调用设备 API:")
        print(f"   端点: {http_method} {api_endpoint}")
        print(f"   设备: {device_id}")
        print(f"   参数: {json.dumps(parameters, indent=6)}")

        # 返回模拟结果
        return {
            "success": True,
            "device_id": device_id,
            "command_executed": request["command_type"],
            "parameters_applied": parameters,
            "executed_at": "2026-04-03T10:30:00Z",
            "message": "指令执行成功"
        }


# ========================================================================
# 场景 3: 完整的使用流程
# ========================================================================

async def complete_workflow_example():
    """
    完整的工作流程示例
    """
    print("=" * 60)
    print("执行提案完整工作流程示例")
    print("=" * 60)

    # 第一步：Agent 生成提案
    print("\n📝 第一步：Agent 生成执行提案")
    print("-" * 60)
    proposal_json = agent_generates_proposal()
    print(proposal_json)

    # 第二步：业务 API 接收并执行
    print("\n⚙️ 第二步：业务 API 接收并执行提案")
    print("-" * 60)

    api_client = DeviceAPIClient()
    result = await api_client.execute_proposal(proposal_json)

    print("\n📊 执行结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


# ========================================================================
# 场景 4: 拒绝的提案示例
# ========================================================================

def rejected_proposal_example():
    """
    展示一个被拒绝的提案
    """
    print("\n" + "=" * 60)
    print("拒绝提案示例")
    print("=" * 60)

    proposal_json = generate_execution_proposal(
        command_type="discharge",
        device_id="dev_002",
        device_type="PCS",
        parameters={
            "power": 1000.0,  # 超出安全范围
            "target_soc": 10
        },
        api_endpoint="/api/v1/devices/pcs/discharge",
        http_method="POST",
        validation_passed=False,  # 未通过验证
        validation_details={
            "parameter_validation": False,  # 参数验证失败
            "safety_check": True,
            "permission_check": True
        },
        risk_level="high",
        risk_factors=["功率超出安全范围 (max: 500kW)", "目标SOC过低"],
        confidence_score=0.85,
        review_summary="指令审查未通过：功率1000kW超出设备安全上限500kW，建议降低功率至安全范围内。",
        operator="system",
        session_id="sess_20260403_002",
        priority=5
    )

    print(proposal_json)

    # 业务 API 接收后
    response = parse_proposal_from_json(proposal_json)
    print(f"\n✅ 提案被安全拒绝: {response.message}")
    print(f"🚫 拒绝原因: {response.error}")


if __name__ == "__main__":
    import asyncio

    # 运行完整流程示例
    asyncio.run(complete_workflow_example())

    # 运行拒绝提案示例
    rejected_proposal_example()
