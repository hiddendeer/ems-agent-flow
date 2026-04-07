"""
MCP 工具集成器。

将 MCP 工具转换为 LangChain 兼容的工具格式，便于在 Agent 中使用。
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from functools import wraps

from langchain_core.tools import tool, StructuredTool
from pydantic import BaseModel, Field

from .client import MCPClient, MCPClientManager
from .exceptions import MCPToolCallError

logger = logging.getLogger(__name__)


def async_tool(func: Callable) -> Callable:
    """
    异步工具装饰器，用于处理 LangChain 工具的异步调用。

    LangChain 的 tool 装饰器默认不支持异步函数，这个装饰器提供了桥接。
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.create_task(func(*args, **kwargs))

    return wrapper


class MCPToolFactory:
    """
    MCP 工具工厂类。

    负责：
    - 从 MCP 服务器获取工具列表
    - 动态创建 Pydantic 模型
    - 生成 LangChain 兼容的工具
    """

    def __init__(self, client_manager: MCPClientManager):
        """
        初始化工具工厂。

        Args:
            client_manager: MCP 客户端管理器
        """
        self.client_manager = client_manager
        self._tool_schemas: Dict[str, Dict[str, Any]] = {}
        self._generated_models: Dict[str, type[BaseModel]] = {}

    async def load_tools_from_server(
        self,
        server_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        从 MCP 服务器加载工具列表。

        Args:
            server_name: 服务器名称

        Returns:
            工具列表
        """
        tools = await self.client_manager.list_tools(server_name)

        for tool_info in tools:
            tool_name = tool_info["name"]
            self._tool_schemas[tool_name] = tool_info

        logger.info(f"从服务器 '{server_name}' 加载了 {len(tools)} 个工具")
        return tools

    def _create_input_model(
        self,
        tool_name: str,
        input_schema: Dict[str, Any]
    ) -> type[BaseModel]:
        """
        动态创建 Pydantic 输入模型。

        Args:
            tool_name: 工具名称
            input_schema: 输入参数 Schema

        Returns:
            Pydantic 模型类
        """
        if tool_name in self._generated_models:
            return self._generated_models[tool_name]

        # 从 Schema 中提取字段定义
        fields: Dict[str, Any] = {}
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        for field_name, field_info in properties.items():
            field_type = self._map_json_type_to_python(field_info.get("type", "string"))
            field_description = field_info.get("description", "")

            # 判断是否为必需字段
            if field_name in required:
                fields[field_name] = (field_type, Field(..., description=field_description))
            else:
                fields[field_name] = (
                    Optional[field_type],
                    Field(None, description=field_description)
                )

        # 动态创建模型类
        model_class = type(
            f"{tool_name.replace('_', ' ').title().replace(' ', '')}Input",
            (BaseModel,),
            {
                "__annotations__": {k: v[0] for k, v in fields.items()},
                **{k: v[1] for k, v in fields.items()},
                "Config": {"extra": "allow"}
            }
        )

        self._generated_models[tool_name] = model_class
        return model_class

    def _map_json_type_to_python(self, json_type: str) -> type:
        """
        将 JSON 类型映射到 Python 类型。

        Args:
            json_type: JSON 类型字符串

        Returns:
            Python 类型
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List[Any],
            "object": Dict[str, Any]
        }
        return type_mapping.get(json_type, str)

    def create_langchain_tool(
        self,
        tool_name: str,
        server_name: Optional[str] = None
    ) -> StructuredTool:
        """
        创建 LangChain 兼容的工具。

        Args:
            tool_name: 工具名称
            server_name: 服务器名称

        Returns:
            LangChain StructuredTool 实例
        """
        if tool_name not in self._tool_schemas:
            raise ValueError(f"未找到工具: {tool_name}")

        tool_info = self._tool_schemas[tool_name]
        tool_description = tool_info["description"]
        input_schema = tool_info.get("inputSchema", {})

        # 创建输入模型
        input_model = self._create_input_model(tool_name, input_schema)

        # 创建异步调用函数
        async def _call_tool(**kwargs) -> str:
            try:
                result = await self.client_manager.call_tool(
                    tool_name=tool_name,
                    arguments=kwargs,
                    server_name=server_name
                )

                # 格式化返回结果
                if isinstance(result, dict):
                    import json
                    return json.dumps(result, ensure_ascii=False, indent=2)
                return str(result)

            except MCPToolCallError as e:
                logger.error(f"调用 MCP 工具失败 ({tool_name}): {e}")
                return f"工具调用失败: {str(e)}"
            except Exception as e:
                logger.exception(f"工具调用异常 ({tool_name}): {e}")
                return f"工具调用异常: {str(e)}"

        # 创建 StructuredTool
        return StructuredTool.from_coroutine(
            name=tool_name,
            description=tool_description,
            func=_call_tool,
            args_schema=input_model
        )

    async def create_all_tools(
        self,
        server_name: Optional[str] = None
    ) -> List[StructuredTool]:
        """
        创建服务器的所有工具。

        Args:
            server_name: 服务器名称

        Returns:
            LangChain 工具列表
        """
        await self.load_tools_from_server(server_name)

        tools = []
        for tool_name in self._tool_schemas.keys():
            try:
                langchain_tool = self.create_langchain_tool(tool_name, server_name)
                tools.append(langchain_tool)
            except Exception as e:
                logger.warning(f"创建工具 '{tool_name}' 失败: {e}")

        logger.info(f"成功创建了 {len(tools)} 个 LangChain 工具")
        return tools

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具的 Schema 信息。

        Args:
            tool_name: 工具名称

        Returns:
            工具 Schema
        """
        return self._tool_schemas.get(tool_name)

    def list_loaded_tools(self) -> List[str]:
        """
        列出已加载的工具名称。

        Returns:
            工具名称列表
        """
        return list(self._tool_schemas.keys())


class MCPToolSet:
    """
    MCP 工具集。

    提供便捷的方式来管理和使用 MCP 工具。
    """

    def __init__(
        self,
        client_manager: MCPClientManager,
        auto_load: bool = True
    ):
        """
        初始化工具集。

        Args:
            client_manager: MCP 客户端管理器
            auto_load: 是否自动加载工具
        """
        self.client_manager = client_manager
        self.factory = MCPToolFactory(client_manager)
        self._tools: Dict[str, List[StructuredTool]] = {}
        self._auto_load = auto_load

    async def load_tools(
        self,
        server_name: Optional[str] = None,
        server_names: Optional[List[str]] = None
    ) -> List[StructuredTool]:
        """
        从服务器加载工具。

        Args:
            server_name: 单个服务器名称
            server_names: 多个服务器名称列表

        Returns:
            加载的工具列表
        """
        if server_names:
            all_tools = []
            for name in server_names:
                tools = await self.factory.create_all_tools(name)
                self._tools[name] = tools
                all_tools.extend(tools)
            return all_tools
        else:
            tools = await self.factory.create_all_tools(server_name)
            server_name = server_name or self.client_manager.config.default_server
            if server_name:
                self._tools[server_name] = tools
            return tools

    def get_tools(self, server_name: Optional[str] = None) -> List[StructuredTool]:
        """
        获取已加载的工具。

        Args:
            server_name: 服务器名称

        Returns:
            工具列表
        """
        if server_name:
            return self._tools.get(server_name, [])

        # 返回所有服务器的工具
        all_tools = []
        for tools in self._tools.values():
            all_tools.extend(tools)
        return all_tools

    def get_tool_by_name(
        self,
        tool_name: str,
        server_name: Optional[str] = None
    ) -> Optional[StructuredTool]:
        """
        根据名称获取工具。

        Args:
            tool_name: 工具名称
            server_name: 服务器名称

        Returns:
            工具实例或 None
        """
        tools = self.get_tools(server_name)
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    def list_tools(self, server_name: Optional[str] = None) -> List[str]:
        """
        列出工具名称。

        Args:
            server_name: 服务器名称

        Returns:
            工具名称列表
        """
        tools = self.get_tools(server_name)
        return [tool.name for tool in tools]

    async def auto_load_tools(self) -> None:
        """
        自动加载所有配置的服务器的工具。
        """
        if not self._auto_load:
            return

        server_names = list(self.client_manager.config.servers.keys())
        await self.load_tools(server_names=server_names)
