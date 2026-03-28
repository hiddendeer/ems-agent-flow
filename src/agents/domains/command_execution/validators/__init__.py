"""
指令执行验证器模块。

提供多维度验证能力：
- 参数验证：检查参数合法性、范围、类型
- 安全检查：检查设备状态、时序冲突、安全阈值
- 权限检查：验证操作权限级别
"""

from .parameter_validator import ParameterValidator, ValidationResult
from .safety_checker import SafetyChecker, SafetyCheckResult, RiskLevel
from .permission_checker import PermissionChecker, PermissionCheckResult

__all__ = [
    "ParameterValidator",
    "ValidationResult",
    "SafetyChecker",
    "SafetyCheckResult",
    "RiskLevel",
    "PermissionChecker",
    "PermissionCheckResult",
]
