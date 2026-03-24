"""
电力市场专用工具集。

包含电价查询、电力政策分析、负荷分析、电网调度等工具。
这些工具仅供 PowerMarketAgent 使用。
"""

from langchain_core.tools import tool
from typing import Literal, Optional
from pydantic import BaseModel, Field

from ....core.resilience import timeout_fallback


class QueryElectricityPriceSchema(BaseModel):
    region: str = Field(
        default="广东", 
        description="省份或地区名称，目前支持中国各主要省份", 
        examples=["广东", "浙江", "江苏"]
    )
    category: Literal["工业", "商业", "居民"] = Field(
        default="工业", 
        description="用电类别划分"
    )

@tool(args_schema=QueryElectricityPriceSchema)
@timeout_fallback(timeout_seconds=15)
def query_electricity_price(region: str = "广东", category: str = "工业") -> str:
    """查询指定地区的分时电价。"""
    # TODO: 对接实际电价数据库或 API
    price_data = {
        "广东": {
            "工业": {
                "尖峰": 1.25, "高峰": 1.15, "平段": 0.65,
                "低谷": 0.32, "深谷": 0.22,
            },
        },
        "浙江": {
            "工业": {
                "尖峰": 1.20, "高峰": 1.08, "平段": 0.62,
                "低谷": 0.30, "深谷": 0.20,
            },
        },
        "江苏": {
            "工业": {
                "峰段": 1.10, "高峰": 1.05, "平段": 0.58,
                "低谷": 0.28,
            },
        },

    }
    
    region_data = price_data.get(region, price_data["广东"])
    cat_data = region_data.get(category, list(region_data.values())[0])
    
    lines = [f"【{region}省{category}用电 - 分时电价】"]
    for period, price in cat_data.items():
        lines.append(f"• {period}时段: {price} 元/kWh")
    
    lines.extend([
        "",
        "【时段划分参考】",
        "• 尖峰: 14:00-15:00, 17:00-19:00",
        "• 高峰: 09:00-12:00, 15:00-17:00, 19:00-22:00",
        "• 平段: 07:00-09:00, 12:00-14:00",
        "• 低谷: 22:00-24:00, 00:00-07:00",
    ])
    
    return "\n".join(lines)


class SearchEnergyPolicySchema(BaseModel):
    keyword: str = Field(
        ..., 
        description="能源电力相关搜索关键词", 
        examples=["新型储能", "需求响应", "虚拟电厂"]
    )

@tool(args_schema=SearchEnergyPolicySchema)
@timeout_fallback(timeout_seconds=15)
def search_energy_policy(keyword: str) -> str:
    """搜索最新的能源电力相关政策。"""
    # 针对江苏省的定制化模拟数据
    if "江苏" in keyword:
        return (
            f"【能源政策搜索 - '{keyword}'】\n\n"
            f"1. 江苏省发改委《关于 2024 年电力市场交易有关事项的通知》\n"
            f"   - 进一步扩大分时电价价差，提高储能经济性\n"
            f"   - 明确了独立储能电站参与辅助服务市场的补偿标准\n\n"
            f"2. 江苏省新型储能“十四五”发展规划\n"
            f"   - 到2025年，全省新型储能装机容量达到 500 万千瓦左右\n"
            f"   - 鼓励多场景应用，重点发展削峰填谷、调频等应用"
        )
    
    # 通用的模拟返回
    return (
        f"【能源政策搜索 - '{keyword}'】\n\n"
        f"1. 《关于加快推动新型储能发展的指导意见》(2024)\n..."
    )


class AnalyzeLoadPatternSchema(BaseModel):
    enterprise_id: str = Field(
        default="ENT-001", 
        description="企业唯一编号标识"
    )
    period: Literal["daily", "weekly", "monthly"] = Field(
        default="daily", 
        description="分析的时间周期粒度"
    )

@tool(args_schema=AnalyzeLoadPatternSchema)
@timeout_fallback(timeout_seconds=15)
def analyze_load_pattern(enterprise_id: str = "ENT-001", period: str = "daily") -> str:
    """分析企业的历史用电负荷模式与峰谷特征。"""
    # TODO: 对接实际负荷数据（InfluxDB）
    return (
        f"【负荷分析 - {enterprise_id} ({period})】\n"
        f"• 日均用电量: 12,500 kWh\n"
        f"• 最大负荷: 2,800 kW (出现在 14:00-15:00)\n"
        f"• 最小负荷: 450 kW (出现在 03:00-05:00)\n"
        f"• 负荷率: 56.3%\n"
        f"• 峰谷差率: 83.9%\n"
        f"• 建议: 峰谷差较大，适合配置储能进行削峰填谷\n"
        f"• 推荐储能容量: 2MWh / 1MW"
    )


class CalculateDemandResponseRevenueSchema(BaseModel):
    capacity_kw: float = Field(
        ..., 
        description="参与响应的可调节电力容量，单位为千瓦(kW)", 
        gt=0
    )
    region: str = Field(
        default="广东", 
        description="所在地区/省份"
    )

@tool(args_schema=CalculateDemandResponseRevenueSchema)
@timeout_fallback(timeout_seconds=15)
def calculate_demand_response_revenue(capacity_kw: float = 1000, region: str = "广东") -> str:
    """计算参与电网侧需求响应的预期补贴与收益。"""
    # TODO: 对接实际需求响应市场价格
    unit_price = 3.5  # 元/kW
    annual_events = 20
    annual_revenue = capacity_kw * unit_price * annual_events
    
    return (
        f"【需求响应收益分析 - {region}】\n"
        f"• 可调节容量: {capacity_kw} kW\n"
        f"• 补贴单价: {unit_price} 元/kW·次\n"
        f"• 预计年参与次数: {annual_events} 次\n"
        f"• 年度预计收益: {annual_revenue:,.0f} 元\n"
        f"• 说明: 参与电网需求响应，在用电高峰时段削减负荷获取补贴"
    )


class GetGridRealtimeStatusSchema(BaseModel):
    region: str = Field(
        default="广东", 
        description="需要查询的电网所在地区/省份"
    )

@tool(args_schema=GetGridRealtimeStatusSchema)
@timeout_fallback(timeout_seconds=15)
def get_grid_realtime_status(region: str = "广东") -> str:
    """获取区域电网的实时运行调度数据与负荷状况。"""
    # TODO: 对接电网调度系统
    return (
        f"【{region}电网实时状况】\n"
        f"• 当前负荷: 98,500 MW\n"
        f"• 最大供电能力: 125,000 MW\n"
        f"• 负载率: 78.8%\n"
        f"• 频率: 50.01 Hz (正常)\n"
        f"• 供需形势: 供需平衡\n"
        f"• 预警等级: 绿色 (正常)"
    )

