"""
PyPSA 建模分析 Agent — 基于 deepagents 框架。
"""

from ...core.domain_agent import DomainAgent
from ...core.registry import AgentRegistry
from .tools import (
    build_and_run_economic_dispatch,
    plan_long_term_infrastructure_investment,
)
from .prompts import PYPSA_MODELING_SYSTEM_PROMPT

class PyPSAModelingAgent(DomainAgent):
    """
    基于 PyPSA 的系统架构与优化求解专家。
    
    能够：
    - 开发并求解线性/非线性的电力调度最优解
    - 多期的综合资源长期规划（含发电、网架、储能）
    - 提供极其定量的充放电策略支撑
    """
    
    def __init__(self):
        super().__init__(
            name="PyPSAModelingExpert",
            description=(
                "电力系统规划与运筹优化建模专家。专门使用 PyPSA 框架"
                "处理微电网经济调度、储能最优充放电动态策略求解、"
                "以及考虑单期或多期、离散/连续决策的基础设施长期投资最低成本推演。"
            ),
        )
    
    def get_tools(self) -> list:
        return [
            build_and_run_economic_dispatch,
            plan_long_term_infrastructure_investment,
        ]
    
    def get_system_prompt(self) -> str:
        return PYPSA_MODELING_SYSTEM_PROMPT

# 自动注册
AgentRegistry.register(PyPSAModelingAgent())
