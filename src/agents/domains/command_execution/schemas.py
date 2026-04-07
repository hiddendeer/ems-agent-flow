"""
执行提案数据模型

定义 Agent 返回给业务层的结构化执行提案格式。
业务 API 根据此提案执行实际的设备操作。
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
import json


class CommandType(str, Enum):
    """指令类型枚举"""
    CHARGE = "charge"
    DISCHARGE = "discharge"
    STOP = "stop"
    STANDBY = "standby"
    RESET = "reset"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProposalStatus(str, Enum):
    """提案状态"""
    PENDING_EXECUTION = "pending_execution"  # 待执行
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    EXECUTING = "executing"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败


class ValidationBackcheck(BaseModel):
    """验证背书信息"""
    passed: bool = Field(..., description="是否通过验证")
    parameter_validation: bool = Field(..., description="参数验证是否通过")
    safety_check: bool = Field(..., description="安全检查是否通过")
    permission_check: bool = Field(..., description="权限检查是否通过")
    validation_timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def dict(self, **kwargs):
        """兼容 Pydantic V2"""
        return self.model_dump(**kwargs)


class RiskAssessment(BaseModel):
    """风险评估信息"""
    risk_level: RiskLevel = Field(..., description="风险等级")
    risk_factors: List[str] = Field(default_factory=list, description="风险因素列表")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="置信度分数")
    assessment_timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def dict(self, **kwargs):
        """兼容 Pydantic V2"""
        return self.model_dump(**kwargs)


class ExecutionParameter(BaseModel):
    """执行参数定义"""
    name: str = Field(..., description="参数名称")
    value: Any = Field(..., description="参数值")
    data_type: str = Field(..., description="数据类型: int/float/str/bool")
    unit: Optional[str] = Field(None, description="单位，如 kW, %, 分钟")
    range: Optional[Dict[str, float]] = Field(None, description="允许范围: {min, max}")
    required: bool = Field(default=True, description="是否必需")


class ExecutionTarget(BaseModel):
    """执行目标定义"""
    device_id: str = Field(..., description="目标设备ID")
    device_type: str = Field(..., description="设备类型: BMS/PCS/METER")
    command_type: CommandType = Field(..., description="指令类型")
    api_endpoint: str = Field(..., description="要调用的API端点")
    http_method: str = Field(default="POST", description="HTTP方法: POST/PUT/PATCH")
    parameters: List[ExecutionParameter] = Field(..., description="执行参数列表")
    timeout_seconds: int = Field(default=30, description="执行超时时间")
    retry_count: int = Field(default=3, description="重试次数")


class AuditTrail(BaseModel):
    """审计追踪信息"""
    proposal_id: str = Field(..., description="提案ID")
    operator: str = Field(..., description="操作员标识")
    agent_name: str = Field(..., description="智能体名称")
    session_id: str = Field(..., description="会话ID")
    parent_request_id: Optional[str] = Field(None, description="父请求ID")
    created_at: datetime = Field(default_factory=datetime.now)
    review_summary: str = Field(..., description="审查总结")
    rejection_reason: Optional[str] = Field(None, description="拒绝原因（如果被拒绝）")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def dict(self, **kwargs):
        """兼容 Pydantic V2"""
        return self.model_dump(**kwargs)


class ExecutionProposal(BaseModel):
    """
    执行提案主模型

    这是 Agent 返回给业务层的核心数据结构。
    业务 API 根据此提案执行实际的设备操作。
    """

    # 添加 datetime 序列化器
    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime) -> str:
        return dt.isoformat()

    @field_serializer('target')
    def serialize_target(self, target: Any) -> Any:
        """序列化 target 对象"""
        if hasattr(target, 'model_dump'):
            return target.model_dump(mode='json')
        return target
    """
    执行提案主模型

    这是 Agent 返回给业务层的核心数据结构。
    业务 API 根据此提案执行实际的设备操作。
    """
    # 基本信息
    proposal_id: str = Field(..., description="提案唯一标识")
    status: ProposalStatus = Field(default=ProposalStatus.PENDING_EXECUTION, description="提案状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    # 执行目标
    target: ExecutionTarget = Field(..., description="执行目标信息")

    # 安全背书
    validation: ValidationBackcheck = Field(..., description="验证背书")
    risk_assessment: RiskAssessment = Field(..., description="风险评估")

    # 审计信息
    audit: AuditTrail = Field(..., description="审计追踪")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    priority: int = Field(default=5, ge=1, le=10, description="优先级 (1-10)")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def dict(self, **kwargs):
        """兼容 Pydantic V2"""
        return self.model_dump(**kwargs)

    def to_execution_request(self) -> Dict[str, Any]:
        """
        转换为执行请求格式

        Returns:
            可直接用于 API 调用的字典
        """
        # 将参数列表转换为字典
        params_dict = {
            param.name: param.value
            for param in self.target.parameters
        }

        return {
            "proposal_id": self.proposal_id,
            "device_id": self.target.device_id,
            "command_type": self.target.command_type.value,
            "api_endpoint": self.target.api_endpoint,
            "http_method": self.target.http_method,
            "parameters": params_dict,
            "timeout": self.target.timeout_seconds,
            "retry_count": self.target.retry_count,
            "priority": self.priority,
            "metadata": {
                "operator": self.audit.operator,
                "session_id": self.audit.session_id,
                "risk_level": self.risk_assessment.risk_level.value,
                "created_at": self.created_at.isoformat()
            }
        }

    def is_safe_to_execute(self) -> bool:
        """判断是否安全可执行"""
        return (
            self.status == ProposalStatus.PENDING_EXECUTION and
            self.validation.passed and
            self.risk_assessment.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        )


class ProposalResponse(BaseModel):
    """
    Agent 返回给业务层的响应格式

    包装执行提案，提供统一的响应格式
    """
    success: bool = Field(..., description="是否成功生成提案")
    message: str = Field(..., description="响应消息")
    proposal: Optional[ExecutionProposal] = Field(None, description="执行提案（如果成功）")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def dict(self, **kwargs):
        """兼容 Pydantic V2"""
        return self.model_dump(**kwargs)


# ========================================================================
# 使用示例
# ========================================================================

if __name__ == "__main__":
    # 示例：创建一个充电指令的执行提案
    proposal = ExecutionProposal(
        proposal_id="PROP-2026-0403-001",
        target=ExecutionTarget(
            device_id="dev_001",
            device_type="PCS",
            command_type=CommandType.CHARGE,
            api_endpoint="/api/v1/devices/pcs/charge",
            http_method="POST",
            parameters=[
                ExecutionParameter(
                    name="power",
                    value=100.0,
                    data_type="float",
                    unit="kW",
                    range={"min": 0, "max": 500}
                ),
                ExecutionParameter(
                    name="target_soc",
                    value=80,
                    data_type="int",
                    unit="%",
                    range={"min": 0, "max": 100}
                )
            ]
        ),
        validation=ValidationBackcheck(
            passed=True,
            parameter_validation=True,
            safety_check=True,
            permission_check=True
        ),
        risk_assessment=RiskAssessment(
            risk_level=RiskLevel.LOW,
            risk_factors=[],
            confidence_score=0.95
        ),
        audit=AuditTrail(
            proposal_id="PROP-2026-0403-001",
            operator="system",
            agent_name="CommandExecutionExpert",
            session_id="sess_12345",
            review_summary="指令通过安全审查，参数合法，建议执行"
        ),
        priority=5,
        tags=["charge", "low-risk"]
    )

    # 输出 JSON 格式
    import json
    print(json.dumps(proposal.dict(by_alias=True, exclude_none=True), indent=2, ensure_ascii=False))

    # 转换为执行请求
    print("\n执行请求格式:")
    print(json.dumps(proposal.to_execution_request(), indent=2, ensure_ascii=False))
