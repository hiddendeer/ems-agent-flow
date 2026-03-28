"""
安全检查器。

检查指令的安全性和设备状态兼容性。
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "严重"


@dataclass
class SafetyCheckResult:
    """安全检查结果"""
    is_safe: bool
    reason: str = ""
    risk_level: str = RiskLevel.LOW.value
    suggestions: List[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class SafetyChecker:
    """
    安全检查器。

    检查维度：
    - 设备状态兼容性
    - 时序冲突检测
    - 安全阈值校验
    - 设备健康度检查
    """

    # 模拟设备状态存储（实际应从数据库或设备接口获取）
    _device_states: Dict[str, Dict[str, Any]] = {
        "BAT-001": {
            "status": "standby",  # standby, charging, discharging, fault, offline
            "soc": 45.0,
            "soh": 98.5,  # State of Health
            "temperature": 25.0,
            "voltage": 380.0,
            "current": 0.0,
            "power": 0.0,
            "capacity": 1000,  # kWh
            "last_update": "2026-03-28T10:00:00Z"
        },
        "BAT-002": {
            "status": "charging",
            "soc": 78.0,
            "soh": 95.2,
            "temperature": 32.0,
            "voltage": 390.0,
            "current": 200.0,
            "power": 78.0,
            "capacity": 500,
            "last_update": "2026-03-28T10:00:00Z"
        },
        "PCS-001": {
            "status": "standby",
            "power": 0.0,
            "efficiency": 95.0,
            "temperature": 40.0,
            "last_update": "2026-03-28T10:00:00Z"
        }
    }

    # 安全阈值
    MAX_TEMPERATURE = 55.0  # ℃
    MAX_SOC_CHARGE = 95.0  # %
    MIN_SOC_DISCHARGE = 10.0  # %
    MAX_POWER_RAMP_RATE = 500  # kW/min（功率爬升率）

    def check(
        self,
        device_id: str,
        command_type: str,
        parameters: Dict[str, Any]
    ) -> SafetyCheckResult:
        """
        执行安全检查。

        Args:
            device_id: 设备ID
            command_type: 指令类型
            parameters: 指令参数

        Returns:
            SafetyCheckResult: 安全检查结果
        """
        # 1. 检查设备是否存在
        if device_id not in self._device_states:
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备不存在: {device_id}",
                risk_level=RiskLevel.HIGH.value,
                suggestions=["检查设备ID是否正确", "确认设备是否已注册"]
            )

        device_state = self._device_states[device_id]

        # 2. 检查设备状态
        status_check = self._check_device_status(device_state, command_type)
        if not status_check.is_safe:
            return status_check

        # 3. 检查SOC限制
        soc_check = self._check_soc_limits(device_state, command_type, parameters)
        if not soc_check.is_safe:
            return soc_check

        # 4. 检查温度限制
        temp_check = self._check_temperature_limits(device_state)
        if not temp_check.is_safe:
            return temp_check

        # 5. 检查功率变化率
        power_check = self._check_power_ramp_rate(device_state, command_type, parameters)
        if not power_check.is_safe:
            return power_check

        # 6. 检查健康度
        health_check = self._check_device_health(device_state)
        if not health_check.is_safe:
            return health_check

        # 所有检查通过
        return SafetyCheckResult(
            is_safe=True,
            reason="所有安全检查通过",
            risk_level=self._calculate_risk_level(device_state, command_type, parameters).value
        )

    def _check_device_status(
        self,
        device_state: Dict[str, Any],
        command_type: str
    ) -> SafetyCheckResult:
        """检查设备状态兼容性"""
        status = device_state.get("status", "")

        # 故障状态
        if status == "fault":
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备处于故障状态，无法执行指令",
                risk_level=RiskLevel.CRITICAL.value,
                suggestions=["先排除设备故障", "联系维护人员"]
            )

        # 离线状态
        if status == "offline":
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备离线，无法执行指令",
                risk_level=RiskLevel.HIGH.value,
                suggestions=["检查设备通信", "确认设备供电"]
            )

        # 时序冲突检测
        if command_type == "charge" and status == "charging":
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备正在充电，无法执行充电指令",
                risk_level=RiskLevel.LOW.value,
                suggestions=["先停止当前充电", "或修改充电参数"]
            )

        if command_type == "discharge" and status == "discharging":
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备正在放电，无法执行放电指令",
                risk_level=RiskLevel.LOW.value,
                suggestions=["先停止当前放电", "或修改放电参数"]
            )

        if command_type == "charge" and status == "discharging":
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备正在放电，不能直接切换到充电",
                risk_level=RiskLevel.MEDIUM.value,
                suggestions=["先停止放电", "等待设备进入待机状态"]
            )

        if command_type == "discharge" and status == "charging":
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备正在充电，不能直接切换到放电",
                risk_level=RiskLevel.MEDIUM.value,
                suggestions=["先停止充电", "等待设备进入待机状态"]
            )

        return SafetyCheckResult(is_safe=True)

    def _check_soc_limits(
        self,
        device_state: Dict[str, Any],
        command_type: str,
        parameters: Dict[str, Any]
    ) -> SafetyCheckResult:
        """检查SOC限制"""
        soc = device_state.get("soc", 0)

        if command_type == "charge":
            target_soc = parameters.get("target_soc", 100)
            if soc >= self.MAX_SOC_CHARGE:
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"当前SOC({soc}%)已达到充电上限({self.MAX_SOC_CHARGE}%)",
                    risk_level=RiskLevel.MEDIUM.value,
                    suggestions=[f"当前SOC过高，不宜继续充电", "建议先放电后再充电"]
                )
            if target_soc > self.MAX_SOC_CHARGE:
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"目标SOC({target_soc}%)超过充电上限({self.MAX_SOC_CHARGE}%)",
                    risk_level=RiskLevel.MEDIUM.value,
                    suggestions=[f"将目标SOC调整为{self.MAX_SOC_CHARGE}%或以下"]
                )

        if command_type == "discharge":
            min_soc = parameters.get("min_soc", 0)
            if soc <= self.MIN_SOC_DISCHARGE:
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"当前SOC({soc}%)已达到放电下限({self.MIN_SOC_DISCHARGE}%)",
                    risk_level=RiskLevel.HIGH.value,
                    suggestions=["立即停止放电", "先充电后再放电"]
                )
            if min_soc < self.MIN_SOC_DISCHARGE:
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"最低SOC({min_soc}%)低于安全下限({self.MIN_SOC_DISCHARGE}%)",
                    risk_level=RiskLevel.HIGH.value,
                    suggestions=[f"将最低SOC调整为{self.MIN_SOC_DISCHARGE}%或以上"]
                )

        return SafetyCheckResult(is_safe=True)

    def _check_temperature_limits(
        self,
        device_state: Dict[str, Any]
    ) -> SafetyCheckResult:
        """检查温度限制"""
        temperature = device_state.get("temperature", 0)

        if temperature >= self.MAX_TEMPERATURE:
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备温度({temperature}℃)超过安全上限({self.MAX_TEMPERATURE}℃)",
                risk_level=RiskLevel.CRITICAL.value,
                suggestions=["立即停止运行", "启动冷却系统", "检查冷却设备"]
            )

        if temperature >= self.MAX_TEMPERATURE - 10:
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备温度({temperature}℃)接近安全上限",
                risk_level=RiskLevel.HIGH.value,
                suggestions=["降低充放电功率", "加强冷却", "密切监控温度"]
            )

        return SafetyCheckResult(is_safe=True)

    def _check_power_ramp_rate(
        self,
        device_state: Dict[str, Any],
        command_type: str,
        parameters: Dict[str, Any]
    ) -> SafetyCheckResult:
        """检查功率变化率"""
        current_power = device_state.get("power", 0)
        target_power = parameters.get("power", 0)

        if command_type in ["charge", "discharge"] and target_power:
            power_change = abs(target_power - current_power)
            # 这里简化处理，实际应考虑时间间隔
            if power_change > self.MAX_POWER_RAMP_RATE * 2:  # 假设2分钟内
                return SafetyCheckResult(
                    is_safe=False,
                    reason=f"功率变化过大({power_change}kW)，超过安全爬升率",
                    risk_level=RiskLevel.MEDIUM.value,
                    suggestions=["分步调整功率", "增加功率变化时间"]
                )

        return SafetyCheckResult(is_safe=True)

    def _check_device_health(
        self,
        device_state: Dict[str, Any]
    ) -> SafetyCheckResult:
        """检查设备健康度"""
        soh = device_state.get("soh", 100)

        if soh < 80:
            return SafetyCheckResult(
                is_safe=False,
                reason=f"设备健康度(SOH: {soh}%)过低，建议维护",
                risk_level=RiskLevel.HIGH.value,
                suggestions=["安排设备维护", "限制充放电功率", "考虑更换电池"]
            )

        if soh < 90:
            return SafetyCheckResult(
                is_safe=True,
                reason="设备健康度偏低，可正常运行但需关注",
                risk_level=RiskLevel.MEDIUM.value,
                suggestions=["定期检查设备状态", "计划维护时间"]
            )

        return SafetyCheckResult(is_safe=True)

    def _calculate_risk_level(
        self,
        device_state: Dict[str, Any],
        command_type: str,
        parameters: Dict[str, Any]
    ) -> RiskLevel:
        """计算综合风险等级"""
        risk_factors = 0

        # 功率越大风险越高
        power = parameters.get("power", 0)
        if power > 1000:
            risk_factors += 1

        # SOC越接近极限风险越高
        soc = device_state.get("soc", 50)
        if soc > 90 or soc < 20:
            risk_factors += 1

        # 温度越高风险越高
        temp = device_state.get("temperature", 25)
        if temp > 45:
            risk_factors += 1

        # 健康度越低风险越高
        soh = device_state.get("soh", 100)
        if soh < 90:
            risk_factors += 1

        # 计算风险等级
        if risk_factors == 0:
            return RiskLevel.LOW
        elif risk_factors <= 2:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH

    def update_device_state(self, device_id: str, state: Dict[str, Any]):
        """更新设备状态（用于模拟）"""
        self._device_states[device_id] = {
            **self._device_states.get(device_id, {}),
            **state,
            "last_update": "2026-03-28T10:00:00Z"
        }
        logger.info(f"设备状态已更新: {device_id}")
