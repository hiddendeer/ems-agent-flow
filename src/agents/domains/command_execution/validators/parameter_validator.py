"""
参数验证器。

验证指令参数的合法性、范围和类型。
"""

from typing import Any, Dict, List
from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    """指令类型枚举"""
    CHARGE = "charge"          # 充电
    DISCHARGE = "discharge"    # 放电
    STOP = "stop"              # 停止
    STANDBY = "standby"        # 待机
    RESET = "reset"            # 复位


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    reason: str = ""
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class ParameterValidator:
    """
    参数验证器。

    验证指令参数的合法性：
    - 参数完整性
    - 参数类型
    - 参数范围
    - 参数组合合法性
    """

    # 参数范围限制
    POWER_MIN = 0  # kW
    POWER_MAX = 5000  # kW
    SOC_MIN = 0  # %
    SOC_MAX = 100  # %
    DURATION_MIN = 0  # 分钟
    DURATION_MAX = 1440  # 分钟（24小时）
    VOLTAGE_MIN = 0  # V
    VOLTAGE_MAX = 1000  # V
    CURRENT_MIN = -1000  # A（负值表示放电）
    CURRENT_MAX = 1000  # A

    def validate(
        self,
        command_type: str,
        parameters: Dict[str, Any]
    ) -> ValidationResult:
        """
        验证指令参数。

        Args:
            command_type: 指令类型
            parameters: 参数字典

        Returns:
            ValidationResult: 验证结果
        """
        # 1. 验证指令类型
        try:
            cmd_type = CommandType(command_type.lower())
        except ValueError:
            return ValidationResult(
                is_valid=False,
                reason=f"无效的指令类型: {command_type}。"
                       f"支持的类型: {[c.value for c in CommandType]}"
            )

        # 2. 根据指令类型验证参数
        if cmd_type == CommandType.CHARGE:
            return self._validate_charge_params(parameters)
        elif cmd_type == CommandType.DISCHARGE:
            return self._validate_discharge_params(parameters)
        elif cmd_type == CommandType.STOP:
            return self._validate_stop_params(parameters)
        elif cmd_type == CommandType.STANDBY:
            return self._validate_standby_params(parameters)
        elif cmd_type == CommandType.RESET:
            return self._validate_reset_params(parameters)

        return ValidationResult(is_valid=True)

    def _validate_charge_params(self, params: Dict[str, Any]) -> ValidationResult:
        """验证充电参数"""
        warnings = []

        # 检查必需参数
        if "power" not in params and "current" not in params:
            return ValidationResult(
                is_valid=False,
                reason="充电指令缺少功率或电流参数"
            )

        # 验证功率参数
        if "power" in params:
            power = params["power"]
            if not isinstance(power, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"功率参数类型错误: {type(power)}，应为数字"
                )
            if not (self.POWER_MIN <= power <= self.POWER_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"功率超出范围: {power}kW。"
                           f"允许范围: {self.POWER_MIN}-{self.POWER_MAX}kW"
                )
            if power <= 0:
                return ValidationResult(
                    is_valid=False,
                    reason="充电功率必须大于0"
                )

        # 验证电流参数
        if "current" in params:
            current = params["current"]
            if not isinstance(current, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"电流参数类型错误: {type(current)}，应为数字"
                )
            if not (self.CURRENT_MIN <= current <= self.CURRENT_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"电流超出范围: {current}A。"
                           f"允许范围: {self.CURRENT_MIN}-{self.CURRENT_MAX}A"
                )
            if current <= 0:
                return ValidationResult(
                    is_valid=False,
                    reason="充电电流必须大于0"
                )

        # 验证目标SOC
        if "target_soc" in params:
            target_soc = params["target_soc"]
            if not isinstance(target_soc, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"SOC参数类型错误: {type(target_soc)}，应为数字"
                )
            if not (self.SOC_MIN <= target_soc <= self.SOC_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"目标SOC超出范围: {target_soc}%。"
                           f"允许范围: {self.SOC_MIN}-{self.SOC_MAX}%"
                )
            if target_soc > 95:
                warnings.append("目标SOC>95%可能影响电池寿命")

        # 验证持续时间
        if "duration" in params:
            duration = params["duration"]
            if not isinstance(duration, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"持续时间类型错误: {type(duration)}，应为数字"
                )
            if not (self.DURATION_MIN <= duration <= self.DURATION_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"持续时间超出范围: {duration}分钟。"
                           f"允许范围: {self.DURATION_MIN}-{self.DURATION_MAX}分钟"
                )

        return ValidationResult(is_valid=True, warnings=warnings)

    def _validate_discharge_params(self, params: Dict[str, Any]) -> ValidationResult:
        """验证放电参数"""
        warnings = []

        # 检查必需参数
        if "power" not in params and "current" not in params:
            return ValidationResult(
                is_valid=False,
                reason="放电指令缺少功率或电流参数"
            )

        # 验证功率参数
        if "power" in params:
            power = params["power"]
            if not isinstance(power, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"功率参数类型错误: {type(power)}，应为数字"
                )
            if not (self.POWER_MIN <= power <= self.POWER_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"功率超出范围: {power}kW。"
                           f"允许范围: {self.POWER_MIN}-{self.POWER_MAX}kW"
                )
            if power <= 0:
                return ValidationResult(
                    is_valid=False,
                    reason="放电功率必须大于0"
                )

        # 验证电流参数
        if "current" in params:
            current = params["current"]
            if not isinstance(current, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"电流参数类型错误: {type(current)}，应为数字"
                )
            if not (self.CURRENT_MIN <= current <= self.CURRENT_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"电流超出范围: {current}A。"
                           f"允许范围: {self.CURRENT_MIN}-{self.CURRENT_MAX}A"
                )
            if current >= 0:
                warnings.append("放电电流应为负值，正值表示充电")

        # 验证最低SOC限制
        if "min_soc" in params:
            min_soc = params["min_soc"]
            if not isinstance(min_soc, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"SOC参数类型错误: {type(min_soc)}，应为数字"
                )
            if not (self.SOC_MIN <= min_soc <= self.SOC_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"最低SOC超出范围: {min_soc}%。"
                           f"允许范围: {self.SOC_MIN}-{self.SOC_MAX}%"
                )
            if min_soc < 10:
                warnings.append("最低SOC<10%可能影响电池寿命")

        # 验证持续时间
        if "duration" in params:
            duration = params["duration"]
            if not isinstance(duration, (int, float)):
                return ValidationResult(
                    is_valid=False,
                    reason=f"持续时间类型错误: {type(duration)}，应为数字"
                )
            if not (self.DURATION_MIN <= duration <= self.DURATION_MAX):
                return ValidationResult(
                    is_valid=False,
                    reason=f"持续时间超出范围: {duration}分钟。"
                           f"允许范围: {self.DURATION_MIN}-{self.DURATION_MAX}分钟"
                )

        return ValidationResult(is_valid=True, warnings=warnings)

    def _validate_stop_params(self, params: Dict[str, Any]) -> ValidationResult:
        """验证停止参数"""
        # 停止指令通常不需要参数，或只需要设备ID
        return ValidationResult(is_valid=True)

    def _validate_standby_params(self, params: Dict[str, Any]) -> ValidationResult:
        """验证待机参数"""
        # 待机指令通常不需要参数
        return ValidationResult(is_valid=True)

    def _validate_reset_params(self, params: Dict[str, Any]) -> ValidationResult:
        """验证复位参数"""
        warnings = []

        # 复位指令需要特别小心
        if "force" in params and params["force"]:
            warnings.append("强制复位可能导致数据丢失")

        return ValidationResult(is_valid=True, warnings=warnings)
