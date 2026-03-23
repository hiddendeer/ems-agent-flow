from typing import Any, Callable, Sequence, List, Dict
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from deepagents.graph import create_deep_agent
from langchain.chat_models import init_chat_model
from deepagents.backends.filesystem import FilesystemBackend
from ..config.settings import settings
import os
from ..tools.system_tools import get_current_time, get_system_info, write_to_file, simulated_search

def get_default_subagents() -> List[Dict[str, Any]]:
    """
    定义电力行业专用的子智能体库。
    """
    return [
        {
            "name": "SearchExpert",
            "description": "电力政策调研专家。负责搜索最新的能源政策、实时市场价格、行业动态等外部联网信息。",
            "system_prompt": "你是一个专业的电力行业调研助手。始终使用相对路径且严禁以 / 开头。运用 simulated_search 工具获取外部电价或政策，并撰写初步结论。",
            "tools": [simulated_search]
        },
        {
            "name": "RAGExpert",
            "description": "电力规程查找专家。专门负责在本地规程文档中进行语义查找。",
            "system_prompt": "你是一个电力技术规程专家。始终使用相对路径且严禁以 / 开头。基于本地背景信息，回答关于电力安全准则和技术参数的问题。",
        },
        {
            "name": "ResultArchiver",
            "description": "结果归档专家。负责将最终的调研报告存档为文件。",
            "system_prompt": (
                "你是一个档案管理员。你的任务是：\n"
                "1. 首先调用 get_current_time 获取当前时间戳字符串。\n"
                "2. 构造文件名，格式为：src/agents/demo/reports/report_时间戳.log (其中'时间戳'替换为刚才获取的值)。\n"
                "3. 调用 write_to_file 工具将接收到的调研报告完整内容写入该文件。\n"
                "4. 报告必须包含所有关键的工业电价数据和规程对比结论。\n"
                "注意：路径严禁以 / 开头，且必须直接执行，不要闲聊。"
            ),
            "tools": [get_current_time, write_to_file] 
        },
        {
            "name": "Executor",
            "description": "业务执行专家。负责处理数据、生成分析报表或特定的控制脚本。",
            "system_prompt": "你是一个电力业务执行专家。始终使用相对路径且严禁以 / 开头。擅长生成高质量的报告文档和执行建议。",
        }
    ]

def agent_factory(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    system_prompt: str | None = None,
    include_subagents: bool = True,
    **kwargs: Any
):
    """
    创建 Deep Agent 的工厂函数。
    """
    target_model = model or settings.DEFAULT_MODEL
    
    if isinstance(target_model, str) and target_model.startswith("openai:"):
        actual_model = init_chat_model(
            target_model,
            base_url=settings.OPENAI_API_BASE,
            api_key=settings.OPENAI_API_KEY
        )
    else:
        actual_model = target_model

    backend = FilesystemBackend(root_dir=os.getcwd(), virtual_mode=False)

    # 准备子智能体配置
    subagents = get_default_subagents() if include_subagents else None

    # 合并工具列表 (默认带上系统工具)
    default_tools = [get_system_info, get_current_time, write_to_file]
    final_tools = list(tools) if tools else default_tools

    # 创建主 Agent
    agent = create_deep_agent(
        model=actual_model,
        tools=final_tools,
        subagents=subagents,
        system_prompt=system_prompt,
        backend=backend,
        debug=settings.DEBUG,
        **kwargs
    )
    
    return agent
