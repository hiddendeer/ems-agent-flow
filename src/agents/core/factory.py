"""
EMS Agent 工厂 — 深度集成 deepagents。
修复：增强中间件对同步/异步 handler 的兼容性。
"""

import os
import platform
import logging
import inspect  # 导入 inspect 模块
from typing import Any, Sequence

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain.agents.middleware.types import AgentMiddleware 

from ..config.settings import settings
from .registry import AgentRegistry

logger = logging.getLogger(__name__)

# --- 跨平台路径修正中间件类 ---

class CrossPlatformPathMiddleware(AgentMiddleware):
    """
    符合 deepagents 规范的路径修正中间件。
    """
    
    def wrap_tool_call(self, request, handler):
        """同步工具调用拦截"""
        new_req = self._preprocess_request(request)
        return handler(new_req)

    async def awrap_tool_call(self, request, handler):
        """异步工具调用拦截 (适配 astream)"""
        new_req = self._preprocess_request(request)
        
        # 核心修正：智能识别是否需要 await
        result = handler(new_req)
        if inspect.isawaitable(result):
            return await result
        return result

    def _preprocess_request(self, request):
        """通用的路径预处理逻辑，返回可能被 override 的 request"""
        # 注意：这里的工具名必须匹配 deepagents 内部定义的工具名
        file_tools = {"write_file", "read_file", "edit_file", "ls", "glob", "grep"}
        
        # 获取最底层的 tool_call 字典
        tool_call = getattr(request, "tool_call", None)
        if not tool_call:
            return request
            
        req_name = tool_call.get("name")
        req_args = tool_call.get("args", {})
        
        if req_name and req_name in file_tools:
            # 兼容深信服 deepagents 文件工具参数名
            arg_keys = ["path", "pattern", "directory", "file_path"]
            
            modified_args = dict(req_args)
            has_changes = False
            
            for key in arg_keys:
                if key in modified_args:
                    path_val = modified_args[key]
                    if path_val and isinstance(path_val, str):
                        # 核心修正：移除错误前缀防止被判断为绝对路径而写到根目录
                        new_path = path_val
                        if new_path.startswith("/"):
                            new_path = new_path.lstrip("/")
                        if new_path.startswith("./"):
                            new_path = new_path[2:]
                        
                        if new_path != path_val:
                            modified_args[key] = new_path
                            has_changes = True
                            sys_name = platform.system()
                            # 使用 logger 记录路径修正
                            logger.info(f"[{sys_name} 路径修正 ({req_name})] '{path_val}' -> '{new_path}'")
            
            # 如果发生了修改，使用内置的 override() 重新组装不可变 request
            if has_changes:
                modified_call = {**tool_call, "args": modified_args}
                return request.override(tool_call=modified_call)
                
        return request


import time

class TimingMiddleware(AgentMiddleware):
    """
    性能监控中间件：记录 LLM 调用和工具调用的耗时。
    """
    
    def wrap_model_call(self, request, handler):
        start = time.time()
        result = handler(request)
        duration = time.time() - start
        logger.debug(f"[LLM Call] 耗时: {duration:.2f}s")
        return result

    async def awrap_model_call(self, request, handler):
        start = time.time()
        result = await handler(request)
        duration = time.time() - start
        logger.debug(f"[LLM Call] 耗时: {duration:.2f}s")
        return result

    def wrap_tool_call(self, request, handler):
        tool_call = getattr(request, "tool_call", {})
        tool_name = tool_call.get("name", "unknown")
        start = time.time()
        result = handler(request)
        duration = time.time() - start
        logger.debug(f"[Tool Call: {tool_name}] 耗时: {duration:.2f}s")
        return result

    async def awrap_tool_call(self, request, handler):
        tool_call = getattr(request, "tool_call", {})
        tool_name = tool_call.get("name", "unknown")
        start = time.time()

        result = handler(request)
        if inspect.isawaitable(result):
            result = await result

        duration = time.time() - start
        logger.debug(f"[Tool Call: {tool_name}] 耗时: {duration:.2f}s")
        return result


# --- EMS 系统级提示词 ---

EMS_LEAD_AGENT_PROMPT = """你是 EMS（智能能源管理系统）的首席协调 Agent，目标是为用户提供**极致响应速度**的专业咨询。

## 核心准则
1. **执行优先 (Fast-Response)** — 收到任务后立即行动。非极度复杂（超过 10 步）的任务，**严禁**在中间过程调用 `write_todos` 进行反复规划。直接利用现有工具获取结果并汇总。
2. **任务分派** — 尽可能一次性分发多个 `task` 任务。
3. **多领域协同 (Multi-Domain Synergy)** — 充分利用子 Agent 的专业知识（如：设备控制、数据建模、市场分析等）。如果是需要多方配合的任务，你应该协调汇总各领域的输出，提供一个综合性的最终方案。
4. **知识沉淀 (Knowledge Retention)** — 每次完成重要的任务（如：设备控制执行、复杂策略产出、重要的用户偏好确认）后，你 **必须** 提取核心事实并使用 `update_user_memory` 工具将其记录到 `notes` 分类中。
5. **语言要求** — **必须使用中文回复**。所有输出（包括思考过程、工具调用说明、最终答案等）必须使用中文，禁止使用英文回复（专业术语除外）。
"""

def create_ems_agent(
    user_id: str = "default_user",
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | list | dict[str, Any]] | None = None,
    system_prompt: str | None = None,
    include_domain_agents: bool = True,
    debug: bool | None = None,
    **kwargs: Any,
):
    """创建 EMS Lead Agent (具备完整功能的生产就绪版)"""
    
    # 1. 模型解析
    target_model = model or settings.DEFAULT_MODEL
    if isinstance(target_model, str) and target_model.startswith("openai:"):
        actual_model = init_chat_model(
            target_model,
            base_url=settings.OPENAI_API_BASE,
            api_key=settings.OPENAI_API_KEY,
        )
    else:
        actual_model = target_model

    # 2. 挂载持久化工作区与沙箱隔离
    project_root = os.path.abspath(os.getcwd())
    from .workspace import WorkspaceManager, create_memory_expert_tool
    workspace_mgr = WorkspaceManager(project_root, user_id)
    
    # 将此用户的专属沙箱工作区作为文件系统的根后台，彻底隔离！
    backend = FilesystemBackend(root_dir=workspace_mgr.get_workspace_dir(), virtual_mode=False)

    # 3. 收集子 Agent
    subagents = []
    if include_domain_agents and AgentRegistry.count() > 0:
        subagents = AgentRegistry.get_subagent_configs()
        # 核心：为子 Agent 也挂载计时监控和长期记忆工具
        memory_tool = create_memory_expert_tool(workspace_mgr)
        for sa in subagents:
            # 注入中间件
            if "middleware" not in sa or sa["middleware"] is None:
                sa["middleware"] = []
            sa["middleware"].append(TimingMiddleware())
            
            # 注入记忆工具，让子 Agent 也能自我记录
            if "tools" not in sa or sa["tools"] is None:
                sa["tools"] = []
            sa["tools"].append(memory_tool)

    # 4. 组装中间件栈 (实例化类)
    middleware_stack = [
        CrossPlatformPathMiddleware(),
        TimingMiddleware(),
    ]
    if "middleware" in kwargs:
        middleware_stack.extend(kwargs.pop("middleware"))

    # 5. 动态计算跨期记忆提示词并注入内存操作组件
    base_prompt = system_prompt or EMS_LEAD_AGENT_PROMPT
    profile_summary = workspace_mgr.get_profile_summary()
    dynamic_sys_prompt = f"{base_prompt}\n\n## 当前用户的长效档案记录 (Memory Profile)\n```json\n{profile_summary}\n```\n务必遵守由档案中规定的偏好与客观参数条件进行调度规划。\n"
    
    final_tools = list(tools) if tools else []
    final_tools.append(create_memory_expert_tool(workspace_mgr))

    # 6. 调用 deepagents 编译
    agent = create_deep_agent(
        model=actual_model,
        tools=final_tools,
        system_prompt=dynamic_sys_prompt,
        subagents=subagents,
        backend=backend,
        middleware=middleware_stack,
        debug=debug if debug is not None else settings.DEBUG,
        **kwargs,
    )

    return agent
