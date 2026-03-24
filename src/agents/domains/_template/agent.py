"""
[领域名称] Agent — 开发模板

使用方法：
1. 复制 _template/ 目录并重命名为你的领域名称
2. 实现 get_tools() 和 get_system_prompt()
3. 在模块底部注册 Agent
4. 在 domains/__init__.py 添加导入

deepagents 框架会自动为每个 SubAgent 提供：
- write_todos (任务规划)
- ls/read_file/write_file/edit_file (文件操作)
- 上下文管理和自动摘要
- 错误处理和中间件栈
"""

from ...core.domain_agent import DomainAgent
from ...core.registry import AgentRegistry
# from .tools import your_tool_1, your_tool_2


class TemplateAgent(DomainAgent):
    """[替换为你的领域 Agent 描述]"""
    
    def __init__(self):
        super().__init__(
            name="TemplateExpert",          # 替换为 Agent 名称
            description="模板专家描述",      # 替换为能力描述
        )
    
    def get_tools(self) -> list:
        """返回领域专属工具列表"""
        return []  # 替换为实际工具
    
    def get_system_prompt(self) -> str:
        """返回领域系统提示词"""
        return "你是一个专业的...(替换为实际提示词)"
    
    # 可选覆盖：
    # def get_model(self) -> str: return "openai:gpt-4o"
    # def get_skills(self) -> list: return ["/skills/my_domain/"]
    # def get_middleware(self) -> list: return [MyCustomMiddleware()]


# 取消注释以启用自动注册:
# AgentRegistry.register(TemplateAgent())
