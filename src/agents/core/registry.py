"""
Agent 注册中心 — 收集领域 Agent 配置，输出 deepagents 兼容格式。

AgentRegistry 不参与 Agent 的运行时。
它只负责：
1. 收集各领域的 DomainAgent 配置描述
2. 批量输出 deepagents SubAgent TypedDict 列表
3. 生成能力摘要文本（注入 Lead Agent 的系统提示词）

运行时由 deepagents 的 SubAgentMiddleware / create_deep_agent 全权负责。
"""

from typing import Dict, Optional, List
from .domain_agent import DomainAgent
import logging

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Agent 注册中心。
    
    全局单例（类方法模式），收集所有领域 DomainAgent 配置，
    批量输出给 create_deep_agent(subagents=...) 使用。
    """
    
    _agents: Dict[str, DomainAgent] = {}

    @classmethod
    def register(cls, agent: DomainAgent) -> None:
        """注册一个领域 Agent"""
        if not isinstance(agent, DomainAgent):
            raise TypeError(
                f"只能注册 DomainAgent 的子类实例，收到: {type(agent).__name__}"
            )
        if agent.name in cls._agents:
            logger.warning(f"Agent '{agent.name}' 已注册，将被覆盖")
        cls._agents[agent.name] = agent
        logger.info(f"✅ 已注册领域 Agent: {agent.name}")

    @classmethod
    def unregister(cls, name: str) -> Optional[DomainAgent]:
        """注销一个领域 Agent"""
        return cls._agents.pop(name, None)

    @classmethod
    def get(cls, name: str) -> Optional[DomainAgent]:
        """按名称获取 Agent"""
        return cls._agents.get(name)

    @classmethod
    def get_all(cls) -> List[DomainAgent]:
        """获取所有已注册的 Agent"""
        return list(cls._agents.values())

    @classmethod
    def get_names(cls) -> List[str]:
        """获取所有已注册的 Agent 名称"""
        return list(cls._agents.keys())

    @classmethod
    def get_subagent_configs(cls) -> list:
        """
        导出所有已注册 Agent 的 deepagents SubAgent 配置列表。
        
        直接传给 create_deep_agent(subagents=...) 使用。
        
        Returns:
            SubAgent TypedDict 列表
        """
        return [agent.to_subagent_config() for agent in cls._agents.values()]

    @classmethod
    def get_capabilities_summary(cls) -> str:
        """
        生成能力摘要文本，注入 Lead Agent 系统提示词。
        
        Returns:
            Markdown 格式的能力摘要
        """
        if not cls._agents:
            return "（当前无已注册的领域 Agent）"
        
        lines = []
        for agent in cls._agents.values():
            cap = agent.get_capabilities()
            lines.append(f"### {cap['name']}")
            lines.append(f"- **职责**: {cap['description']}")
            if cap["tools"]:
                tool_names = ", ".join(cap["tools"])
                lines.append(f"- **工具**: {tool_names}")
            lines.append("")
        return "\n".join(lines)

    @classmethod
    def count(cls) -> int:
        return len(cls._agents)

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._agents.clear()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name in cls._agents
