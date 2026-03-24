"""
储能系统专用工具集。

包含电池管理、PCS 变流器控制、充放电策略等工具。
这些工具仅供 EnergyStorageAgent 使用，不暴露给其他领域 Agent。
"""

from langchain_core.tools import tool
from typing import Literal, Optional
from pydantic import BaseModel, Field

from ....core.resilience import timeout_fallback


class GetBatteryStatusSchema(BaseModel):
    device_id: str = Field(
        default="BAT-001",
        description="目标电池设备/簇的全局唯一编号"
    )

@tool(args_schema=GetBatteryStatusSchema)
@timeout_fallback(timeout_seconds=15)
def get_battery_status(device_id: str = "BAT-001") -> str:
    """获取储能电池的实时运行状态信息与健康度评估。"""
    # TODO: 对接实际 BMS 数据源（InfluxDB / Modbus）
    return (
        f"【电池状态 - {device_id}】\n"
        f"• SOC (荷电状态): 65.2%\n"
        f"• SOH (健康状态): 92.5%\n"
        f"• 电压: 750.8V\n"
        f"• 电流: -120.5A (放电中)\n"
        f"• 温度: 28.3°C (正常)\n"
        f"• 循环次数: 1,247 次\n"
        f"• 额定容量: 2MWh\n"
        f"• 运行模式: 削峰填谷"
    )


class GetPcsStatusSchema(BaseModel):
    device_id: str = Field(
        default="PCS-001",
        description="PCS（变流器）设备的全局唯一编号"
    )

@tool(args_schema=GetPcsStatusSchema)
@timeout_fallback(timeout_seconds=15)
def get_pcs_status(device_id: str = "PCS-001") -> str:
    """获取 PCS 储能变流器的实时电量转换操作参数与运行状态。"""
    # TODO: 对接实际 PCS 设备数据
    return (
        f"【PCS 状态 - {device_id}】\n"
        f"• 有功功率: -500kW (放电)\n"
        f"• 无功功率: 50kVar\n"
        f"• 运行模式: 恒功率放电\n"
        f"• 交流侧电压: 380V\n"
        f"• 直流侧电压: 750V\n"
        f"• 效率: 96.8%\n"
        f"• 状态: 运行中"
    )


class SetChargeModeSchema(BaseModel):
    mode: Literal["charge", "discharge", "standby", "auto"] = Field(
        ...,
        description="需要切换的系统运行模式"
    )
    power_kw: float = Field(
        default=500.0,
        description="目标执行的充放电绝对功率(kW)，非负值",
        ge=0
    )
    device_id: str = Field(
        default="PCS-001",
        description="需要控制的 PCS 变流器设备编号"
    )

@tool(args_schema=SetChargeModeSchema)
@timeout_fallback(timeout_seconds=15)
def set_charge_mode(
    mode: str,
    power_kw: float = 500.0,
    device_id: str = "PCS-001",
) -> str:
    """设定储能硬件系统的底层充放电运行模式。下发实际的物理控制指令。"""
    mode_names = {
        "charge": "恒功率充电",
        "discharge": "恒功率放电",
        "standby": "热备待机",
        "auto": "智能自动调度",
    }
    mode_name = mode_names.get(mode, mode)
    
    # TODO: 对接实际控制指令下发
    return (
        f"✅ 模式切换成功\n"
        f"• 设备: {device_id}\n"
        f"• 新模式: {mode_name}\n"
        f"• 目标功率: {power_kw}kW\n"
        f"• 生效时间: 即时"
    )


class CalculateArbitrageProfitSchema(BaseModel):
    peak_price: float = Field(
        ...,
        description="目标城市当前高峰时间的电价 (元/kWh)",
        gt=0
    )
    valley_price: float = Field(
        ...,
        description="目标城市低谷时间的电价 (元/kWh)",
        gt=0
    )
    capacity_kwh: float = Field(
        default=2000.0,
        description="执行套利的储能系统容量配置 (kWh)",
        gt=0
    )
    efficiency: float = Field(
        default=0.92,
        description="该系统的综合充放电圆周率/效率，应在(0,1)区间",
        gt=0,
        lt=1
    )

@tool(args_schema=CalculateArbitrageProfitSchema)
@timeout_fallback(timeout_seconds=15)
def calculate_arbitrage_profit(
    peak_price: float,
    valley_price: float,
    capacity_kwh: float = 2000.0,
    efficiency: float = 0.92,
) -> str:
    """计算储能系统的峰谷套利经济收益预估模型。"""
    charge_cost = valley_price * capacity_kwh
    discharge_revenue = peak_price * capacity_kwh * efficiency
    daily_profit = discharge_revenue - charge_cost
    monthly_profit = daily_profit * 30
    yearly_profit = daily_profit * 365
    
    return (
        f"【峰谷套利收益分析】\n"
        f"• 储能容量: {capacity_kwh}kWh\n"
        f"• 高峰电价: {peak_price}元/kWh\n"
        f"• 低谷电价: {valley_price}元/kWh\n"
        f"• 综合效率: {efficiency*100}%\n"
        f"─────────────────\n"
        f"• 充电成本: {charge_cost:.1f}元\n"
        f"• 放电收入: {discharge_revenue:.1f}元\n"
        f"• 单日收益: {daily_profit:.1f}元\n"
        f"• 月度收益: {monthly_profit:.1f}元\n"
        f"• 年度收益: {yearly_profit:.1f}元"
    )


@tool
@timeout_fallback(timeout_seconds=15)
def get_charge_schedule() -> str:
    """获取今天内已编排的 24 小时完整充放电调度运行计划预设时间表。"""
    # TODO: 从调度系统获取实际数据
    return (
        "【今日充放电调度计划】\n"
        "• 00:00-07:00  充电 (低谷)  500kW\n"
        "• 07:00-09:00  待机\n"
        "• 09:00-12:00  放电 (高峰)  800kW\n"
        "• 12:00-14:00  待机\n"
        "• 14:00-17:00  放电 (高峰)  800kW\n"
        "• 17:00-19:00  放电 (尖峰)  1000kW\n"
        "• 19:00-22:00  待机\n"
        "• 22:00-24:00  充电 (低谷)  500kW"
    )

