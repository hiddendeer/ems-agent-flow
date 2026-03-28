"""
领域 Agent 目录 — 按业务领域组织的 Sub Agent 集合。

当前支持的领域：
- energy_storage: 储能系统 Agent
- power: 电力市场 Agent
- search: 电力情报搜索 Agent
- pypsa_modeling: PyPSA 建模分析 Agent
- command_execution: 指令执行与安全审查 Agent

扩展新领域：
1. 在本目录下新建领域包（可参考 _template/）
2. 继承 DomainAgent 实现领域 Agent
3. 在 agent.py 底部调用 AgentRegistry.register() 自注册
4. 在本文件的 register_all_domains() 中导入该领域
"""

import logging

logger = logging.getLogger(__name__)


def register_all_domains():
    """
    注册所有领域 Agent。
    
    在应用启动时调用此函数，自动发现并注册所有领域 Agent。
    每个领域包的 __init__.py 会自动触发 AgentRegistry.register()。
    """
    # 导入各领域模块 → 触发自注册
    from . import energy_storage  # noqa: F401
    from . import power           # noqa: F401
    from . import search          # noqa: F401  # 电力情报搜索领域
    from . import pypsa_modeling  # noqa: F401  # 最低成本长期系统规划调度领域
    from . import command_execution  # noqa: F401  # 指令执行与安全审查领域
    
    from ..core.registry import AgentRegistry
    logger.info(
        f"🌐 领域 Agent 全部注册完毕，共 {AgentRegistry.count()} 个: "
        f"{AgentRegistry.get_names()}"
    )
