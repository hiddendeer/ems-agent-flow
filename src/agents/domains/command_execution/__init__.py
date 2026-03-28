"""
指令执行领域 Agent 包。

电力储能系统的安全执行层，负责：
- 指令审查与验证
- 设备指令执行
- 风险评估
- 操作日志记录
- 紧急控制

架构：
- agent.py: CommandExecutionAgent 主智能体
- tools/: 工具集（审查、执行、日志、应急）
- validators/: 验证器（参数、安全、权限）
- audit/: 审计模块（日志、审计追踪）
- skills/: 技能知识库（SOP、安全协议）
"""

from .agent import CommandExecutionAgent

__all__ = ["CommandExecutionAgent"]
