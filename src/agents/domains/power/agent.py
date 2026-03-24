"""
电力市场 Agent — 基于 deepagents 框架的领域 Agent 配置。

继承 DomainAgent（配置描述器），声明电力市场领域的工具和提示词。
运行时完全由 deepagents 的 SubAgentMiddleware 负责编译和执行。
"""

from ...core.domain_agent import DomainAgent
from ...core.registry import AgentRegistry
from .tools import (
    query_electricity_price,
    search_energy_policy,
    analyze_load_pattern,
    calculate_demand_response_revenue,
    get_grid_realtime_status,
)
from .prompts import POWER_MARKET_SYSTEM_PROMPT


class PowerMarketAgent(DomainAgent):
    """
    电力市场领域 Agent 配置。
    
    领域覆盖：
    - 电价分析：分时电价政策解读、趋势分析
    - 政策研究：新能源政策、电力市场化改革
    - 负荷管理：企业用电特性分析
    - 需求响应：策略制定和收益评估
    - 电网调度：运行状态监控
    """
    
    def __init__(self):
        super().__init__(
            name="PowerMarketExpert",
            description=(
                "电力市场专家。负责电价分析(分时电价/电价趋势)、"
                "能源政策调研、企业负荷分析、需求响应策略、"
                "电网调度状态监控等全部电力市场领域任务。"
            ),
        )
    
    def get_tools(self) -> list:
        """返回电力市场领域专属工具"""
        return [
            query_electricity_price,
            search_energy_policy,
            analyze_load_pattern,
            calculate_demand_response_revenue,
            get_grid_realtime_status,
        ]
    
    def get_system_prompt(self) -> str:
        """返回电力市场领域系统提示词"""
        return POWER_MARKET_SYSTEM_PROMPT
    
    def get_skills(self) -> list[str]:
        """
        重写父类的方法，加载自定义业务知识/能力包。
        返回的是挂载自定义技能文本档案的绝对路径目录列表。
        """
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        skill_dir = os.path.join(current_dir, "skills")
        return [skill_dir]


# 自动注册到 AgentRegistry
AgentRegistry.register(PowerMarketAgent())
