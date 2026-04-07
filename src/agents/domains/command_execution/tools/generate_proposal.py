"""
生成执行提案工具

将 Agent 的决策转换为结构化的执行提案，供业务 API 调用。
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import json
import uuid
from datetime import datetime

from ..schemas import (
    ExecutionProposal,
    ProposalResponse,
    ProposalStatus,
    CommandType,
    RiskLevel,
    ExecutionTarget,
    ExecutionParameter,
    ValidationBackcheck,
    RiskAssessment,
    AuditTrail
)


class GenerateProposalSchema(BaseModel):
    """生成提案的参数"""
    command_type: str = Field(
        ...,
        description="指令类型: charge/discharge/stop/standby/reset"
    )
    device_id: str = Field(..., description="目标设备ID")
    device_type: str = Field(..., description="设备类型: BMS/PCS/METER")
    parameters: Dict[str, Any] = Field(
        ...,
        description="执行参数，如 {\"power\": 100.0, \"target_soc\": 80}"
    )
    api_endpoint: str = Field(
        ...,
        description="要调用的API端点，如 /api/v1/devices/pcs/charge"
    )
    http_method: str = Field(
        default="POST",
        description="HTTP方法: POST/PUT/PATCH"
    )
    validation_passed: bool = Field(..., description="是否通过验证")
    validation_details: Dict[str, bool] = Field(
        ...,
        description="验证详情: {parameter_validation: bool, safety_check: bool, permission_check: bool}"
    )
    risk_level: str = Field(..., description="风险等级: low/medium/high/critical")
    risk_factors: List[str] = Field(
        default_factory=list,
        description="风险因素列表"
    )
    confidence_score: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="置信度分数 (0.0-1.0)"
    )
    review_summary: str = Field(
        ...,
        description="审查总结，说明为什么通过/拒绝"
    )
    operator: str = Field(default="system", description="操作员标识")
    session_id: str = Field(default="unknown", description="会话ID")
    priority: int = Field(default=5, ge=1, le=10, description="优先级 (1-10)")
    timeout_seconds: int = Field(default=30, description="执行超时时间(秒)")
    retry_count: int = Field(default=3, description="重试次数")


@tool(args_schema=GenerateProposalSchema)
def generate_execution_proposal(
    command_type: str,
    device_id: str,
    device_type: str,
    parameters: Dict[str, Any],
    api_endpoint: str,
    http_method: str = "POST",
    validation_passed: bool = True,
    validation_details: Dict[str, bool] = None,
    risk_level: str = "low",
    risk_factors: List[str] = None,
    confidence_score: float = 0.9,
    review_summary: str = "",
    operator: str = "system",
    session_id: str = "unknown",
    priority: int = 5,
    timeout_seconds: int = 30,
    retry_count: int = 3
) -> str:
    """
    生成结构化的执行提案。

    此工具将 Agent 的审查和评估结果转换为标准化的执行提案格式，
    供业务 API 层解析和执行。

    工作流程：
    1. 接收审查结果和执行参数
    2. 生成唯一提案ID
    3. 构建结构化提案对象
    4. 返回 JSON 格式的提案

    业务 API 接收到提案后：
    1. 验证提案签名（防止伪造）
    2. 检查设备状态
    3. 提取执行参数
    4. 调用目标 API 端点
    5. 记录执行结果
    """
    # 生成唯一提案ID
    proposal_id = f"PROP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

    # 如果验证详情为空，使用默认值
    if validation_details is None:
        validation_details = {
            "parameter_validation": validation_passed,
            "safety_check": validation_passed,
            "permission_check": validation_passed
        }

    # 如果风险因素为空，使用空列表
    if risk_factors is None:
        risk_factors = []

    # 转换参数为列表格式
    parameter_list = []
    for key, value in parameters.items():
        param = ExecutionParameter(
            name=key,
            value=value,
            data_type=type(value).__name__,
            unit=_infer_unit(key),
            required=True
        )
        parameter_list.append(param)

    # 构建执行提案
    try:
        proposal = ExecutionProposal(
            proposal_id=proposal_id,
            status=ProposalStatus.PENDING_EXECUTION if validation_passed else ProposalStatus.REJECTED,
            target=ExecutionTarget(
                device_id=device_id,
                device_type=device_type,
                command_type=CommandType(command_type),
                api_endpoint=api_endpoint,
                http_method=http_method,
                parameters=parameter_list,
                timeout_seconds=timeout_seconds,
                retry_count=retry_count
            ),
            validation=ValidationBackcheck(
                passed=validation_passed,
                parameter_validation=validation_details.get("parameter_validation", False),
                safety_check=validation_details.get("safety_check", False),
                permission_check=validation_details.get("permission_check", False)
            ),
            risk_assessment=RiskAssessment(
                risk_level=RiskLevel(risk_level),
                risk_factors=risk_factors,
                confidence_score=confidence_score
            ),
            audit=AuditTrail(
                proposal_id=proposal_id,
                operator=operator,
                agent_name="CommandExecutionExpert",
                session_id=session_id,
                review_summary=review_summary,
                rejection_reason=None if validation_passed else review_summary
            ),
            priority=priority
        )

        # 构建响应
        response = ProposalResponse(
            success=validation_passed,
            message=f"执行提案已生成: {proposal_id}" if validation_passed else f"提案已拒绝: {proposal_id}",
            proposal=proposal,
            error=None if validation_passed else review_summary
        )

        # 转换为 JSON 字符串返回
        return json.dumps(
            response.dict(by_alias=True, exclude_none=True),
            indent=2,
            ensure_ascii=False
        )

    except Exception as e:
        # 如果生成提案失败，返回错误响应
        error_response = ProposalResponse(
            success=False,
            message=f"生成提案失败: {str(e)}",
            proposal=None,
            error=str(e)
        )
        return json.dumps(
            error_response.dict(by_alias=True, exclude_none=True),
            indent=2,
            ensure_ascii=False
        )


def _infer_unit(param_name: str) -> Optional[str]:
    """根据参数名推断单位"""
    unit_map = {
        "power": "kW",
        "target_soc": "%",
        "soc": "%",
        "soh": "%",
        "voltage": "V",
        "current": "A",
        "temperature": "°C",
        "duration": "分钟",
        "frequency": "Hz",
        "capacity": "kWh"
    }
    return unit_map.get(param_name.lower())


# ========================================================================
# 辅助函数
# ========================================================================

def parse_proposal_from_json(json_str: str) -> ProposalResponse:
    """
    从 JSON 字符串解析提案响应

    Args:
        json_str: JSON 格式的提案字符串

    Returns:
        ProposalResponse 对象
    """
    data = json.loads(json_str)
    return ProposalResponse(**data)


def validate_proposal_signature(proposal: ExecutionProposal) -> bool:
    """
    验证提案签名（防止伪造）

    TODO: 实现签名验证逻辑
    """
    # 这里应该实现签名验证
    # 例如：验证提案中的 HMAC 签名
    return True


__all__ = [
    "generate_execution_proposal",
    "parse_proposal_from_json",
    "validate_proposal_signature"
]
