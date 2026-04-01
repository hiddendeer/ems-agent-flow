"""
设备管理领域 Agent — 动态业务接口智能体。
"""

from typing import List, Optional
from ...core.domain_agent import DomainAgent
from ...core.registry import AgentRegistry
from .tools.device_tools import (
    list_business_interfaces,
    get_interface_definition_schema,
    execute_business_action
)
from .prompts import DEVICE_MANAGEMENT_SYSTEM_PROMPT


class DeviceManagementAgent(DomainAgent):
    """
    EMS 设备管理专家（通用接口驱动型）。
    
    能够：
    - 动态发现业务清单 (Discovery)
    - 获取接口 JSON Schema 定义 (Analysis)
    - 引导用户补齐必要的接口入参 (Prompting)
    - 代理执行最终的业务逻辑并响应 (Execution)
    """
    
    def __init__(self):
        super().__init__(
            name="DeviceManagementExpert",
            description=(
                "EMS 通用业务管理专家。具备动态对接业务子系统的能力：\n"
                "- 支持自动发现并执行各种设备录入、状态更新、数据配置等业务接口\n"
                "- 能够分析并解释接口入参的业务含义及限制条件\n"
                "- 作为业务侧与用户侧的动态桥梁，确保操作合法且闭环"
            ),
        )
    
    def get_tools(self) -> List:
        """返回设备管理专属的通用接口工具集。"""
        return [
            list_business_interfaces,           # 业务清单
            get_interface_definition_schema,    # 获取接口参数定义
            execute_business_action             # 执行业务操作 (网关模式)
        ]
    
    def get_system_prompt(self) -> str:
        """返回设备管理专家的系统提示词。"""
        return DEVICE_MANAGEMENT_SYSTEM_PROMPT

    def get_skills(self) -> Optional[List[str]]:
        """
        [可选] 返回设备管理特有的知识库/业务规范。
        """
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        skill_dir = os.path.join(current_dir, "skills")
        if os.path.exists(skill_dir):
            return [skill_dir]
        return None


# 自动注册到 AgentRegistry
AgentRegistry.register(DeviceManagementAgent())
