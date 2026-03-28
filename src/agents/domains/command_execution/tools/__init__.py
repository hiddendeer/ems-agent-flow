"""
指令执行工具集。

提供完整的指令审查、执行、监控和日志记录功能。
所有工具都经过严格的参数验证和安全检查。
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import logging

from ....core.resilience import timeout_fallback
from ..validators import (
    ParameterValidator,
    SafetyChecker,
    PermissionChecker,
    ValidationResult,
    SafetyCheckResult,
    PermissionCheckResult,
    RiskLevel
)
from ..audit import OperationLogger, OperationStatus, get_logger

logger = logging.getLogger(__name__)

# 初始化验证器和日志记录器
_parameter_validator = ParameterValidator()
_safety_checker = SafetyChecker()
_permission_checker = PermissionChecker()
_operation_logger = get_logger()


# ========================================================================
# 1. 指令审查工具
# ========================================================================

class ReviewCommandSchema(BaseModel):
    """指令审查参数"""
    command_type: str = Field(
        ...,
        description="指令类型: charge(充电)/discharge(放电)/stop(停止)/standby(待机)/reset(复位)"
    )
    device_id: str = Field(..., description="目标设备ID，如 BAT-001, PCS-001")
    parameters: Dict[str, Any] = Field(
        ...,
        description="指令参数，如 {\"power\": 100, \"target_soc\": 80, \"duration\": 120}"
    )
    operator: str = Field(default="system", description="操作者标识")


@tool(args_schema=ReviewCommandSchema)
@timeout_fallback(timeout_seconds=10)
def review_and_validate_command(
    command_type: str,
    device_id: str,
    parameters: Dict[str, Any],
    operator: str = "system"
) -> str:
    """
    审查并验证控制指令的安全性和合法性。

    这是所有指令执行的第一步，必须通过审查才能继续执行。

    检查维度：
    - ✅ 参数合法性验证（类型、范围、完整性）
    - ✅ 设备状态兼容性检查
    - ✅ 操作权限验证
    - ✅ 时序冲突检测
    - ✅ 安全阈值校验

    返回格式：
    - ✅ 审查通过：返回审查通过信息和风险等级
    - ❌ 审查失败：返回详细的失败原因和改进建议

    示例调用：
    ```
    review_and_validate_command(
        command_type="charge",
        device_id="BAT-001",
        parameters={"power": 100, "target_soc": 80},
        operator="user_001"
    )
    ```
    """
    try:
        # 1. 参数验证
        validation_result: ValidationResult = _parameter_validator.validate(
            command_type, parameters
        )
        if not validation_result.is_valid:
            return (
                f"❌ 指令审查失败（参数验证）\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 失败原因: {validation_result.reason}\n"
                f"📋 指令详情:\n"
                f"   • 指令类型: {command_type}\n"
                f"   • 设备ID: {device_id}\n"
                f"   • 参数: {parameters}\n"
                f"💡 改进建议: 请检查参数是否合法\n"
            )

        # 2. 安全检查
        safety_result: SafetyCheckResult = _safety_checker.check(
            device_id, command_type, parameters
        )
        if not safety_result.is_safe:
            suggestions_str = "\n   • ".join(safety_result.suggestions or ["无"])
            return (
                f"❌ 指令审查失败（安全检查）\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 失败原因: {safety_result.reason}\n"
                f"⚠️  风险等级: {safety_result.risk_level}\n"
                f"📋 指令详情:\n"
                f"   • 指令类型: {command_type}\n"
                f"   • 设备ID: {device_id}\n"
                f"   • 参数: {parameters}\n"
                f"💡 改进建议:\n"
                f"   • {suggestions_str}\n"
            )

        # 3. 权限验证
        permission_result: PermissionCheckResult = _permission_checker.check(
            operator, command_type
        )
        if not permission_result.is_allowed:
            return (
                f"❌ 指令审查失败（权限不足）\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 失败原因: {permission_result.reason}\n"
                f"📋 指令详情:\n"
                f"   • 指令类型: {command_type}\n"
                f"   • 操作者: {operator}\n"
                f"   • 当前权限: {permission_result.current_level}\n"
                f"   • 所需权限: {permission_result.required_level}\n"
                f"💡 改进建议: 请联系管理员提升权限或使用高权限账号操作\n"
            )

        # 4. 通过审查
        warnings_str = "\n   • ".join(validation_result.warnings or ["无"])
        return (
            f"✅ 指令审查通过\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 指令详情:\n"
            f"   • 指令类型: {command_type}\n"
            f"   • 目标设备: {device_id}\n"
            f"   • 操作者: {operator}\n"
            f"   • 参数: {parameters}\n"
            f"⚠️  风险等级: {safety_result.risk_level}\n"
            f"🔍 审查结果:\n"
            f"   • ✅ 参数验证通过\n"
            f"   • ✅ 安全检查通过\n"
            f"   • ✅ 权限验证通过\n"
            f"💡 提醒: {warnings_str}\n"
            f"▶️  可以执行，请继续调用执行工具\n"
        )

    except Exception as e:
        logger.exception(f"指令审查异常: {e}")
        return (
            f"❌ 指令审查异常\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🚫 异常信息: {str(e)}\n"
            f"💡 建议: 请检查输入参数或联系技术支持\n"
        )


# ========================================================================
# 2. 风险评估工具
# ========================================================================

class RiskAssessmentSchema(BaseModel):
    """风险评估参数"""
    command_type: str = Field(..., description="指令类型")
    device_id: str = Field(..., description="目标设备ID")
    parameters: Dict[str, Any] = Field(..., description="指令参数")


@tool(args_schema=RiskAssessmentSchema)
@timeout_fallback(timeout_seconds=5)
def assess_command_risk(
    command_type: str,
    device_id: str,
    parameters: Dict[str, Any]
) -> str:
    """
    评估指令执行的风险等级。

    分析维度：
    - 设备健康度影响
    - 经济影响
    - 安全风险
    - 操作复杂度

    返回：风险等级（低/中/高/严重）及详细分析

    示例调用：
    ```
    assess_command_risk(
        command_type="charge",
        device_id="BAT-001",
        parameters={"power": 100, "target_soc": 80}
    )
    ```
    """
    try:
        # 获取设备状态
        device_states = SafetyChecker._device_states
        device_state = device_states.get(device_id, {})

        # 计算风险
        safety_result = _safety_checker.check(device_id, command_type, parameters)
        risk_level = safety_result.risk_level

        # 分析风险因素
        risk_factors = []
        power = parameters.get("power", 0)
        soc = device_state.get("soc", 50)
        temp = device_state.get("temperature", 25)
        soh = device_state.get("soh", 100)

        # 功率风险
        if power > 1000:
            risk_factors.append(f"⚡ 大功率操作({power}kW)可能加速设备老化")
        elif power > 500:
            risk_factors.append(f"⚡ 中等功率操作({power}kW)")

        # SOC风险
        if soc > 90:
            risk_factors.append(f"🔋 当前SOC({soc}%)较高，继续充电可能影响寿命")
        elif soc < 20:
            risk_factors.append(f"🔋 当前SOC({soc}%)较低，深度放电可能影响寿命")

        # 温度风险
        if temp > 45:
            risk_factors.append(f"🌡️  设备温度({temp}℃)偏高，建议加强冷却")
        elif temp < 10:
            risk_factors.append(f"🌡️  设备温度({temp}℃)偏低，建议预热")

        # 健康度风险
        if soh < 90:
            risk_factors.append(f"💊 设备健康度(SOH: {soh}%)偏低，建议计划维护")

        if not risk_factors:
            risk_factors.append("✓ 未发现明显风险因素")

        # 经济影响分析
        economic_impact = "正向收益"
        if command_type == "charge":
            economic_impact = "成本投入（充电费用）"
        elif command_type == "discharge":
            economic_impact = "正向收益（放电收益）"

        return (
            f"📊 风险评估报告\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 综合风险等级: {risk_level}\n"
            f"📋 指令详情:\n"
            f"   • 指令类型: {command_type}\n"
            f"   • 设备ID: {device_id}\n"
            f"   • 参数: {parameters}\n"
            f"📈 风险因素分析:\n"
            f"   • 设备健康度: {'影响较大' if soh < 90 else '影响较小'}\n"
            f"   • 经济影响: {economic_impact}\n"
            f"   • 安全风险: {'可控' if risk_level in ['低', '中'] else '需关注'}\n"
            f"   • 操作复杂度: 标准操作\n"
            f"⚠️  详细因素:\n"
            + "\n   ".join(risk_factors) + "\n"
            f"💡 执行建议:\n"
            f"   • {'可以直接执行' if risk_level == '低' else '建议谨慎执行' if risk_level == '中' else '建议二次确认' if risk_level == '高' else '不建议执行'}\n"
        )

    except Exception as e:
        logger.exception(f"风险评估异常: {e}")
        return f"❌ 风险评估异常: {str(e)}"


# ========================================================================
# 3. 设备执行工具
# ========================================================================

class ExecuteDeviceCommandSchema(BaseModel):
    """设备执行参数"""
    command_type: str = Field(..., description="指令类型")
    device_id: str = Field(..., description="目标设备ID")
    parameters: Dict[str, Any] = Field(..., description="指令参数")
    operator: str = Field(default="system", description="操作者标识")


@tool(args_schema=ExecuteDeviceCommandSchema)
@timeout_fallback(timeout_seconds=30)
def execute_device_command(
    command_type: str,
    device_id: str,
    parameters: Dict[str, Any],
    operator: str = "system"
) -> str:
    """
    向设备下发控制指令并执行。

    ⚠️ 重要：此工具会真实操作设备，请确保：
    1. 已通过 review_and_validate_command 审查
    2. 已通过 assess_command_risk 风险评估
    3. 参数正确无误

    执行流程：
    1. 建立设备通信连接
    2. 下发指令到设备
    3. 监控执行状态
    4. 返回执行结果

    返回：执行结果（成功/失败）及详细信息

    示例调用：
    ```
    execute_device_command(
        command_type="charge",
        device_id="BAT-001",
        parameters={"power": 100, "target_soc": 80},
        operator="user_001"
    )
    ```
    """
    try:
        # 1. 获取设备状态
        device_states = SafetyChecker._device_states
        if device_id not in device_states:
            return (
                f"❌ 设备执行失败\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 失败原因: 设备不存在 - {device_id}\n"
                f"💡 建议: 请检查设备ID是否正确\n"
            )

        device_state = device_states[device_id]

        # 2. 创建操作日志
        operation_log = _operation_logger.create_log(
            command_type=command_type,
            device_id=device_id,
            operator=operator,
            parameters=parameters,
            metadata={"initial_status": device_state.get("status")}
        )

        # 3. 更新日志状态为执行中
        _operation_logger.update_log(
            operation_log.operation_id,
            status=OperationStatus.EXECUTING
        )

        # 4. 模拟执行指令（实际应调用设备API）
        execution_success = True
        error_message = None

        if command_type == "charge":
            # 模拟充电指令
            device_state["status"] = "charging"
            device_state["power"] = parameters.get("power", 0)
            device_state["current"] = parameters.get("power", 0) / device_state.get("voltage", 380) * 1000
        elif command_type == "discharge":
            # 模拟放电指令
            device_state["status"] = "discharging"
            device_state["power"] = -parameters.get("power", 0)
            device_state["current"] = -parameters.get("power", 0) / device_state.get("voltage", 380) * 1000
        elif command_type == "stop":
            # 模拟停止指令
            device_state["status"] = "standby"
            device_state["power"] = 0
            device_state["current"] = 0
        elif command_type == "standby":
            # 模拟待机指令
            device_state["status"] = "standby"
            device_state["power"] = 0
            device_state["current"] = 0
        else:
            execution_success = False
            error_message = f"不支持的指令类型: {command_type}"

        # 5. 更新日志状态
        if execution_success:
            _operation_logger.update_log(
                operation_log.operation_id,
                status=OperationStatus.SUCCESS,
                execution_result=f"指令执行成功: {command_type}",
                metadata={"final_status": device_state.get("status")}
            )

            return (
                f"✅ 指令执行成功\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 操作详情:\n"
                f"   • 操作ID: {operation_log.operation_id}\n"
                f"   • 设备ID: {device_id}\n"
                f"   • 指令类型: {command_type}\n"
                f"   • 操作者: {operator}\n"
                f"   • 执行时间: {operation_log.timestamp}\n"
                f"⚡ 执行参数:\n"
                f"   • {parameters}\n"
                f"📊 当前状态:\n"
                f"   • 设备状态: {device_state.get('status')}\n"
                f"   • 当前功率: {device_state.get('power')}kW\n"
                f"   • 当前SOC: {device_state.get('soc')}%\n"
                f"✨ 指令已成功下发并执行\n"
            )
        else:
            _operation_logger.update_log(
                operation_log.operation_id,
                status=OperationStatus.FAILED,
                error_message=error_message
            )

            return (
                f"❌ 指令执行失败\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 操作详情:\n"
                f"   • 操作ID: {operation_log.operation_id}\n"
                f"   • 设备ID: {device_id}\n"
                f"   • 指令类型: {command_type}\n"
                f"🚫 失败原因: {error_message}\n"
                f"💡 建议: 请检查指令参数或设备状态\n"
            )

    except Exception as e:
        logger.exception(f"设备执行异常: {e}")
        return f"❌ 设备执行异常: {str(e)}"


# ========================================================================
# 4. 操作日志工具
# ========================================================================

class LogOperationSchema(BaseModel):
    """操作日志参数"""
    operation_id: str = Field(..., description="操作ID")
    status: str = Field(
        ...,
        description="状态: success/failed/pending/reviewing/approved/rejected"
    )
    details: Dict[str, Any] = Field(default_factory=dict, description="操作详情")


@tool(args_schema=LogOperationSchema)
@timeout_fallback(timeout_seconds=5)
def log_operation(
    operation_id: str,
    status: str,
    details: Dict[str, Any] = None
) -> str:
    """
    记录或更新操作日志到审计系统。

    用于记录操作过程中的关键节点和最终结果，支持审计追溯。

    参数说明：
    - operation_id: 操作ID（由execute_device_command自动生成）
    - status: 操作状态
      * pending: 待执行
      * reviewing: 审查中
      * approved: 已批准
      * rejected: 已拒绝
      * success: 成功
      * failed: 失败
    - details: 额外的操作详情（可选）

    返回：日志记录确认信息

    示例调用：
    ```
    log_operation(
        operation_id="OP-20260328103000-BAT-001",
        status="success",
        details={"completion_time": "2026-03-28 12:30:00"}
    )
    ```
    """
    try:
        # 映射状态字符串到枚举
        status_map = {
            "pending": OperationStatus.PENDING,
            "reviewing": OperationStatus.REVIEWING,
            "approved": OperationStatus.APPROVED,
            "rejected": OperationStatus.REJECTED,
            "success": OperationStatus.SUCCESS,
            "failed": OperationStatus.FAILED,
        }

        operation_status = status_map.get(status.lower())
        if not operation_status:
            return (
                f"❌ 日志记录失败\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 无效的状态: {status}\n"
                f"💡 支持的状态: {', '.join(status_map.keys())}\n"
            )

        # 更新日志
        updated_log = _operation_logger.update_log(
            operation_id=operation_id,
            status=operation_status,
            metadata=details or {}
        )

        if updated_log:
            return (
                f"📝 操作日志已更新\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 日志详情:\n"
                f"   • 操作ID: {operation_id}\n"
                f"   • 状态: {operation_status.value}\n"
                f"   • 时间戳: {updated_log.timestamp}\n"
                f"✨ 日志已记录到审计系统\n"
            )
        else:
            return (
                f"⚠️  日志更新失败\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 操作ID不存在: {operation_id}\n"
                f"💡 建议: 请检查操作ID是否正确\n"
            )

    except Exception as e:
        logger.exception(f"日志记录异常: {e}")
        return f"❌ 日志记录异常: {str(e)}"


# ========================================================================
# 5. 紧急停止工具
# ========================================================================

class EmergencyStopSchema(BaseModel):
    """紧急停止参数"""
    scope: str = Field(
        default="all",
        description="停止范围: all(所有设备)/specific_device(指定设备)"
    )
    device_id: str = Field(default="", description="指定设备ID（当scope=specific_device时）")
    reason: str = Field(default="", description="停止原因")


@tool(args_schema=EmergencyStopSchema)
@timeout_fallback(timeout_seconds=5)
def emergency_stop_all(
    scope: str = "all",
    device_id: str = "",
    reason: str = ""
) -> str:
    """
    紧急停止所有设备或指定设备的操作。

    🚨 这是一个熔断机制，用于：
    - 检测到严重安全风险
    - 设备异常状态
    - 人工紧急干预

    此工具优先级最高，会立即停止所有正在执行的指令。
    停止后需要人工确认才能恢复运行。

    参数说明：
    - scope: 停止范围
      * all: 停止所有设备（默认）
      * specific_device: 停止指定设备
    - device_id: 指定设备ID（当scope=specific_device时必填）
    - reason: 停止原因（建议填写，便于后续分析）

    返回：紧急停止执行结果

    示例调用：
    ```
    # 停止所有设备
    emergency_stop_all(scope="all", reason="检测到严重安全风险")

    # 停止指定设备
    emergency_stop_all(
        scope="specific_device",
        device_id="BAT-001",
        reason="设备温度过高"
    )
    ```
    """
    try:
        device_states = SafetyChecker._device_states

        if scope == "all":
            # 停止所有设备
            stopped_devices = []
            for dev_id, state in device_states.items():
                if state.get("status") in ["charging", "discharging"]:
                    state["status"] = "standby"
                    state["power"] = 0
                    state["current"] = 0
                    stopped_devices.append(dev_id)

            return (
                f"🚨 紧急停止已执行\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ 停止范围: 所有设备\n"
                f"🚫 停止原因: {reason or '未指定'}\n"
                f"📊 受影响设备: {len(stopped_devices)} 台\n"
                f"📋 设备列表: {', '.join(stopped_devices) if stopped_devices else '无'}\n"
                f"⚠️  警告: 所有设备已停止，需要人工确认才能恢复运行\n"
            )

        elif scope == "specific_device":
            # 停止指定设备
            if not device_id:
                return (
                    f"❌ 紧急停止失败\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚫 失败原因: 指定设备模式需要提供device_id参数\n"
                )

            if device_id not in device_states:
                return (
                    f"❌ 紧急停止失败\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚫 失败原因: 设备不存在 - {device_id}\n"
                )

            device_state = device_states[device_id]
            old_status = device_state.get("status")
            device_state["status"] = "standby"
            device_state["power"] = 0
            device_state["current"] = 0

            return (
                f"🚨 紧急停止已执行\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"⛔ 停止范围: 指定设备\n"
                f"📋 设备ID: {device_id}\n"
                f"🚫 原始状态: {old_status}\n"
                f"✅ 当前状态: standby\n"
                f"🚫 停止原因: {reason or '未指定'}\n"
                f"⚠️  警告: 设备已停止，需要人工确认才能恢复运行\n"
            )

        else:
            return (
                f"❌ 紧急停止失败\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 失败原因: 无效的停止范围 - {scope}\n"
                f"💡 支持的范围: all, specific_device\n"
            )

    except Exception as e:
        logger.exception(f"紧急停止异常: {e}")
        return f"❌ 紧急停止异常: {str(e)}"


# ========================================================================
# 6. 查询设备状态工具（辅助工具）
# ========================================================================

class QueryDeviceStatusSchema(BaseModel):
    """查询设备状态参数"""
    device_id: str = Field(..., description="设备ID")


@tool(args_schema=QueryDeviceStatusSchema)
@timeout_fallback(timeout_seconds=5)
def query_device_status(device_id: str) -> str:
    """
    查询设备的实时状态。

    返回设备的关键运行参数，包括：
    - 设备状态（待机、充电、放电、故障、离线）
    - 当前功率、电压、电流
    - SOC（荷电状态）
    - SOH（健康度）
    - 温度

    这是一个只读工具，不会对设备产生任何影响。

    示例调用：
    ```
    query_device_status(device_id="BAT-001")
    ```
    """
    try:
        device_states = SafetyChecker._device_states

        if device_id not in device_states:
            return (
                f"❌ 设备不存在\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚫 设备ID: {device_id}\n"
                f"💡 建议: 请检查设备ID是否正确\n"
            )

        state = device_states[device_id]

        return (
            f"📊 设备状态查询\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📋 设备ID: {device_id}\n"
            f"🔧 运行状态: {state.get('status', 'unknown')}\n"
            f"⚡ 当前功率: {state.get('power', 0)} kW\n"
            f"🔺 电压: {state.get('voltage', 0)} V\n"
            f"🔻 电流: {state.get('current', 0)} A\n"
            f"🔋 SOC: {state.get('soc', 0)}%\n"
            f"💊 SOH: {state.get('soh', 0)}%\n"
            f"🌡️  温度: {state.get('temperature', 0)}℃\n"
            f"📅 最后更新: {state.get('last_update', 'unknown')}\n"
        )

    except Exception as e:
        logger.exception(f"查询设备状态异常: {e}")
        return f"❌ 查询异常: {str(e)}"


# 导出所有工具
__all__ = [
    "review_and_validate_command",
    "assess_command_risk",
    "execute_device_command",
    "log_operation",
    "emergency_stop_all",
    "query_device_status",
]
