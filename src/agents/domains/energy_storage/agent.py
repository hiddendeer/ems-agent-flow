"""
储能系统 Agent — 基于 deepagents 框架的领域 Agent 配置。

继承 DomainAgent（配置描述器），声明储能领域的工具、提示词和技能。
运行时完全由 deepagents 的 SubAgentMiddleware 负责编译和执行。
"""

from ...core.domain_agent import DomainAgent
from ...core.registry import AgentRegistry
from .tools import (
    get_battery_status,
    get_pcs_status,
    set_charge_mode,
    calculate_arbitrage_profit,
    get_charge_schedule,
)
from .prompts import ENERGY_STORAGE_SYSTEM_PROMPT


class EnergyStorageAgent(DomainAgent):
    """
    储能系统领域 Agent 配置。
    
    领域覆盖：
    - 电池管理系统 (BMS)：SOC/SOH 监控
    - PCS 变流器控制：功率调节与模式切换  
    - 充放电策略：峰谷套利、削峰填谷
    - 经济性分析：投资回报、套利收益
    """
    
    def __init__(self):
        super().__init__(
            name="EnergyStorageExpert",
            description=(
                "储能系统专家。负责电池管理(BMS)、PCS控制、"
                "充放电策略制定(峰谷套利/削峰填谷)、SOC优化、"
                "储能经济性分析等全部储能领域任务。"
            ),
        )
    
    def get_tools(self) -> list:
        """返回储能领域专属工具"""
        return [
            get_battery_status,
            get_pcs_status,
            set_charge_mode,
            calculate_arbitrage_profit,
            get_charge_schedule,
        ]
    
    def get_system_prompt(self) -> str:
        """返回储能领域系统提示词"""
        return ENERGY_STORAGE_SYSTEM_PROMPT


# 自动注册到 AgentRegistry
AgentRegistry.register(EnergyStorageAgent())
