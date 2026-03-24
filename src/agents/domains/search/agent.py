"""
电力情报搜索 Agent — 基于 deepagents 框架。

继承 DomainAgent，专门负责电力行业的互联网搜索、研报扫描和竞争情报追踪。
作为 Lead Agent 的“外部眼线”，为决策提供最新数据基础。
"""

from ...core.domain_agent import DomainAgent
from ...core.registry import AgentRegistry
from .tools import (
    internet_search_power_policy,
    search_market_research_reports,
    track_competitor_dynamics,
)
from .prompts import POWER_SEARCH_SYSTEM_PROMPT


class PowerSearchAgent(DomainAgent):
    """
    电力领域搜索与情报专家。
    
    能够：
    - 检索最新的电力/能源政策
    - 获取电力市场、储能、VPP 的研报摘要
    - 追踪宁德时代、特斯拉等行业巨头的竞争态势
    """
    
    def __init__(self):
        super().__init__(
            name="PowerSearchExpert",
            description=(
                "电力情报搜索专家。专门负责互联网搜索、"
                "电力政策检索、能源研报扫描、"
                "竞争情报追踪等外部数据获取任务。"
            ),
        )
    
    def get_tools(self) -> list:
        """返回搜索专用工具集"""
        return [
            internet_search_power_policy,
            search_market_research_reports,
            track_competitor_dynamics,
        ]
    
    def get_system_prompt(self) -> str:
        """返回搜索专家提示词"""
        return POWER_SEARCH_SYSTEM_PROMPT


# 自动注册到 AgentRegistry
AgentRegistry.register(PowerSearchAgent())
