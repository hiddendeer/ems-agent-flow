"""
Agent Core 模块 — 基于 deepagents 框架的轻量封装层。

不重复实现 deepagents 已有能力，只提供：
- DomainAgent: 领域 Agent 配置基类（生成 deepagents SubAgent 字典）
- AgentRegistry: Agent 注册中心
- create_ems_agent: 创建 EMS 主 Agent 的便捷函数
"""

from .domain_agent import DomainAgent
from .registry import AgentRegistry
from .factory import create_ems_agent

__all__ = [
    "DomainAgent",
    "AgentRegistry",
    "create_ems_agent",
]
