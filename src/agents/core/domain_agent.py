"""
DomainAgent — 领域 Agent 配置基类。

核心设计理念：
    不重新实现 Agent 运行时，只提供一个『配置描述器』。
    每个领域 Agent 继承 DomainAgent，声明自己的名称、描述、工具、技能和提示词，
    最终通过 to_subagent_config() 方法输出 deepagents 原生的 SubAgent TypedDict 格式。

    deepagents 框架的 SubAgentMiddleware 会负责：
    - 将 SubAgent 编译为可执行的 LangGraph 子图
    - 注册 `task()` 工具让 Lead Agent 可以调度子 Agent
    - 自动注入 TodoList、Filesystem、Summarization 等中间件栈
    - 上下文隔离、结果回传

使用方式：
    class MyAgent(DomainAgent):
        name = "MyExpert"
        description = "..."
        
        def get_tools(self): return [my_tool]
        def get_system_prompt(self): return "..."
    
    # 注册中心会收集所有 DomainAgent 并传给 create_deep_agent(subagents=...)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence
from pydantic import BaseModel, Field, ConfigDict
from deepagents.middleware.subagents import SubAgent

class DomainAgentSchema(BaseModel):
    """
    Pydantic 模型：用于领域 Agent 的内部配置硬性校验。
    保证必需字段完整，名字不超过限制等。
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = Field(..., max_length=50, description="Agent 唯一名称标识")
    description: str = Field(..., min_length=10, description="对大模型展示的能力路由描述")
    system_prompt: str = Field(..., min_length=10, description="领域专用的系统提示词")
    tools: list[Any] = Field(..., description="专有工具列表")
    skills: Optional[List[str]] = Field(default=None, description="绑定的知识库/技能树路径")
    model: Optional[str] = Field(default=None, description="定制的大语言模型标识")
    middleware: Optional[list[Any]] = Field(default=None, description="额外的原生中间件")

class DomainAgent(ABC):
    """
    领域 Agent 配置基类。
    
    每个领域（储能、电力等）继承此类，声明自己的：
    - 名称和描述 → 供 Lead Agent 做任务路由
    - 工具列表 → 该领域的专用工具集
    - 系统提示词 → 该领域的角色定义和工作指令
    - （可选）技能路径 → deepagents 原生 Skills 系统
    - （可选）模型覆盖 → 为特定领域使用不同的 LLM
    
    不包含任何运行时逻辑 — 运行时完全交给 deepagents 框架。
    """
    
    def __init__(self, name: str, description: str):
        """
        Args:
            name: Agent 唯一名称（deepagents 的 subagent_type 标识）
            description: 能力描述（Lead Agent 据此决定是否委派任务）
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def get_tools(self) -> list:
        """返回该领域的专用工具列表。"""
        ...
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """返回该领域的系统提示词。"""
        ...
    
    def get_skills(self) -> Optional[List[str]]:
        """返回该领域的 deepagents Skills 路径列表（可选）。"""
        return None
    
    def get_model(self) -> Optional[str]:
        """返回该领域要使用的 LLM 模型标识（可选覆盖）。"""
        return None
    
    def get_middleware(self) -> Optional[list]:
        """返回该领域额外的中间件列表（可选）。"""
        return None
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        返回该 Agent 的结构化能力描述。（用于调试和日志）
        """
        tools = self.get_tools()
        return {
            "name": self.name,
            "description": self.description,
            "tools": [getattr(t, "name", str(t)) for t in tools],
            "model_override": self.get_model(),
        }
    
    def to_subagent_config(self) -> SubAgent:
        """
        转换为 deepagents 原生的 SubAgent TypedDict 配置。
        引入了 Pydantic 校验层，若配置不符合规范（例如 description 过短、tools 为空等异常），
        将在启动时直接抛出 ValidationError 熔断。
        
        Returns:
            符合 deepagents SubAgent 格式的配置字典
        """
        # 1. 使用 Pydantic 进行内部全量校验
        schema = DomainAgentSchema(
            name=self.name,
            description=self.description,
            system_prompt=self.get_system_prompt(),
            tools=self.get_tools(),
            skills=self.get_skills(),
            model=self.get_model(),
            middleware=self.get_middleware()
        )
        
        # 2. 导出为 deepagents 需要的 TypedDict 形式 (去除 None 值的可选参数)
        config: dict = {
            "name": schema.name,
            "description": schema.description,
            "system_prompt": schema.system_prompt,
            "tools": schema.tools,
        }
        
        if schema.model is not None:
            config["model"] = schema.model
        if schema.skills is not None:
            config["skills"] = schema.skills
        if schema.middleware is not None:
            config["middleware"] = schema.middleware
            
        return config  # type: ignore[return-value]
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}'>"
