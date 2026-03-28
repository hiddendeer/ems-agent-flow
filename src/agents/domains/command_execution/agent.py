"""
指令执行 Agent — 电力储能系统的安全执行层。

继承 DomainAgent，专门负责：
- 接收并审查来自决策层的控制指令
- 验证指令安全性、合法性和可执行性
- 与底层设备（BMS/PCS）通信并执行指令
- 记录完整操作日志，支持审计追溯

作为 Lead Agent 的"执行臂"和"安全门"，确保所有操作安全可控。
"""

from typing import List, Optional
from ...core.domain_agent import DomainAgent
from ...core.registry import AgentRegistry
from .tools import (
    review_and_validate_command,
    assess_command_risk,
    execute_device_command,
    log_operation,
    emergency_stop_all,
    query_device_status,
)
from .prompts import COMMAND_EXECUTION_SYSTEM_PROMPT


class CommandExecutionAgent(DomainAgent):
    """
    电力储能指令执行与安全审查专家。

    核心能力：
    - 🔒 指令安全审查：参数范围、时序冲突、操作权限
    - ⚡ 设备指令执行：与 BMS/PCS/EMS 通信
    - 📊 风险评估：操作风险量化、建议替代方案
    - 📝 审计日志：完整记录操作轨迹
    - 🚨 紧急控制：快速熔断、紧急停止

    工作流程：
    1. 接收 Lead Agent 下达的指令
    2. 多维度审查（参数、安全、权限）
    3. 风险评估
    4. 执行或拒绝指令
    5. 记录完整日志
    6. 返回执行结果

    安全原则：
    - 安全第一：宁可拒绝也不冒险
    - 审查优先：所有指令必须通过审查
    - 完整记录：支持审计追溯
    - 快速响应：异常情况立即熔断
    """

    def __init__(self):
        super().__init__(
            name="CommandExecutionExpert",
            description=(
                "电力储能设备指令执行与安全审查专家。"
                "负责接收 Lead Agent 的控制指令，进行严格的安全审查、"
                "权限验证和风险评估后，与底层设备（BMS、PCS、电表等）"
                "通信执行，并记录完整的操作日志供审计追溯。"
                "\n\n"
                "核心功能："
                "\n- 🔒 指令安全审查（参数、状态、权限、冲突检测）"
                "\n- ⚡ 设备指令执行（充电、放电、停止、待机）"
                "\n- 📊 风险评估（健康度、经济性、安全性）"
                "\n- 📝 操作日志（完整审计追踪）"
                "\n- 🚨 紧急控制（熔断保护）"
                "\n\n"
                "工作原则：安全第一、审查优先、完整记录、快速响应。"
            ),
        )

    def get_tools(self) -> List:
        """
        返回执行专用工具集。

        工具分类：
        1. 审查工具：review_and_validate_command
        2. 评估工具：assess_command_risk
        3. 执行工具：execute_device_command
        4. 日志工具：log_operation
        5. 应急工具：emergency_stop_all
        6. 辅助工具：query_device_status
        """
        return [
            review_and_validate_command,      # 指令审查
            assess_command_risk,              # 风险评估
            execute_device_command,           # 设备执行
            log_operation,                    # 操作日志
            emergency_stop_all,               # 紧急停止
            query_device_status,              # 查询状态
        ]

    def get_system_prompt(self) -> str:
        """
        返回执行专家提示词。

        提示词强调：
        - 安全第一原则
        - 严格的审查流程
        - 完整的日志记录
        - 标准的输出格式
        """
        return COMMAND_EXECUTION_SYSTEM_PROMPT

    def get_skills(self) -> Optional[List[str]]:
        """
        返回执行规范和安全协议技能目录列表。

        技能文件包含：
        - 标准作业程序(SOP)
        - 安全阈值参考
        - 风险评估标准
        - 应急处理流程

        Returns:
            技能文件路径列表
        """
        from pathlib import Path
        skills_path = Path(__file__).parent / "skills"
        # 返回技能目录下的 .md 文件列表
        if skills_path.exists():
            return [str(f) for f in skills_path.glob("*.md")]
        return None


# 自动注册到 AgentRegistry
# 这样在系统启动时会自动发现并注册此智能体
AgentRegistry.register(CommandExecutionAgent())
