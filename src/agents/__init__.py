"""
agents 包 — EMS 智能能源管理系统的 Agent 层。

基于 deepagents 框架构建的 Lead Agent + Sub Agent 架构。

deepagents 提供的核心运行时能力：
- Planning (write_todos): 任务规划和分解
- Filesystem (read_file/write_file/edit_file/ls/glob/grep): 文件操作
- Shell (execute): 命令执行
- SubAgent (task): 子 Agent 调度和上下文隔离
- Summarization: 自动上下文压缩
- Middleware: 可扩展的中间件栈

本层（agents 包）提供的领域封装：
- DomainAgent: 领域 Agent 配置基类
- AgentRegistry: Agent 注册中心
- create_ems_agent: 创建 EMS Lead Agent 的便捷函数
- domains/: 按领域组织的 Sub Agent（储能、电力等）

快速使用：
    from src.agents import create_ems_agent, register_all_domains
    
    register_all_domains()
    agent = create_ems_agent()
    result = await agent.ainvoke({
        "messages": [("user", "调研广东省电价并制定储能策略")]
    })
"""

from .core.domain_agent import DomainAgent
from .core.registry import AgentRegistry
from .core.factory import create_ems_agent


def register_all_domains():
    """注册所有领域 Agent（在创建 EMS Agent 之前调用）"""
    from .domains import register_all_domains as _register
    _register()


__all__ = [
    "create_ems_agent",
    "register_all_domains",
    "DomainAgent",
    "AgentRegistry",
]
