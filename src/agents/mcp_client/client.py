"""
MCP 客户端核心实现。

提供统一的 MCP 客户端接口，支持多种传输方式和服务器配置。
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from .config import MCPServerConfig, MCPClientConfig, MCPTransportType
from .exceptions import (
    MCPClientError,
    MCPConnectionError,
    MCPToolCallError,
    MCPInitializationError,
    MCPTimeoutError
)

logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP 客户端类。

    支持与 MCP 服务器进行通信，包括：
    - 连接管理
    - 工具调用
    - 工具列表查询
    - 资源访问
    - 提示词模板访问
    """

    def __init__(
        self,
        server_config: MCPServerConfig,
        server_name: str = "default"
    ):
        """
        初始化 MCP 客户端。

        Args:
            server_config: MCP 服务器配置
            server_name: 服务器名称（用于日志和标识）
        """
        self.server_config = server_config
        self.server_name = server_name
        self._session = None
        self._read_stream = None
        self._write_stream = None
        self._is_connected = False
        self._tools_cache: Optional[List[Dict[str, Any]]] = None
        self._cache_timestamp: Optional[datetime] = None

    async def connect(self) -> None:
        """
        连接到 MCP 服务器。

        Raises:
            MCPConnectionError: 连接失败
            MCPInitializationError: 初始化失败
        """
        try:
            if self.server_config.transport_type == MCPTransportType.STDIO:
                await self._connect_stdio()
            elif self.server_config.transport_type == MCPTransportType.SSE:
                await self._connect_sse()
            elif self.server_config.transport_type == MCPTransportType.WEBSOCKET:
                await self._connect_websocket()
            else:
                raise MCPConnectionError(
                    f"不支持的传输类型: {self.server_config.transport_type}"
                )

            await self._initialize_session()
            self._is_connected = True
            logger.info(f"✅ MCP 客户端 '{self.server_name}' 连接成功")

        except Exception as e:
            logger.error(f"❌ MCP 客户端 '{self.server_name}' 连接失败: {e}")
            raise MCPConnectionError(f"连接失败: {e}") from e

    async def _connect_stdio(self) -> None:
        """使用 STDIO 方式连接"""
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            raise MCPConnectionError(
                "缺少 mcp 依赖包。请安装: pip install mcp"
            )

        command, args, env = self.server_config.get_stdio_params()

        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env or {}
        )

        try:
            self._read_stream, self._write_stream = await asyncio.wait_for(
                stdio_client(server_params),
                timeout=self.server_config.timeout
            )
        except asyncio.TimeoutError:
            raise MCPTimeoutError(
                f"STDIO 连接超时（{self.server_config.timeout}秒）"
            )

    async def _connect_sse(self) -> None:
        """使用 SSE 方式连接"""
        raise NotImplementedError("SSE 传输方式暂未实现")

    async def _connect_websocket(self) -> None:
        """使用 WebSocket 方式连接"""
        raise NotImplementedError("WebSocket 传输方式暂未实现")

    async def _initialize_session(self) -> None:
        """初始化 MCP 会话"""
        try:
            from mcp import ClientSession
        except ImportError:
            raise MCPInitializationError("缺少 mcp 依赖包")

        self._session = ClientSession(self._read_stream, self._write_stream)

        try:
            await asyncio.wait_for(
                self._session.initialize(),
                timeout=self.server_config.timeout
            )
        except asyncio.TimeoutError:
            raise MCPTimeoutError(
                f"MCP 会话初始化超时（{self.server_config.timeout}秒）"
            )

    async def disconnect(self) -> None:
        """断开与 MCP 服务器的连接"""
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                logger.warning(f"关闭 MCP 会话时出错: {e}")

        self._is_connected = False
        self._session = None
        self._read_stream = None
        self._write_stream = None
        logger.info(f"MCP 客户端 '{self.server_name}' 已断开连接")

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        retry: bool = True
    ) -> Any:
        """
        调用 MCP 工具。

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            retry: 是否在失败时重试

        Returns:
            工具执行结果

        Raises:
            MCPToolCallError: 工具调用失败
        """
        if not self._is_connected:
            await self.connect()

        max_attempts = self.server_config.max_retries if retry else 1

        for attempt in range(max_attempts):
            try:
                result = await asyncio.wait_for(
                    self._session.call_tool(tool_name, arguments),
                    timeout=self.server_config.timeout
                )

                # 处理返回结果
                if hasattr(result, "content") and result.content:
                    content = result.content[0]
                    if hasattr(content, "text"):
                        text = content.text
                        # 尝试解析为 JSON
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            return text
                    return content

                return result

            except asyncio.TimeoutError:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"工具调用超时: {tool_name}，"
                        f"正在重试 ({attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(self.server_config.retry_delay)
                else:
                    raise MCPTimeoutError(
                        f"工具调用超时: {tool_name} "
                        f"（超过 {max_attempts} 次重试）"
                    )

            except Exception as e:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"工具调用失败: {tool_name} - {e}，"
                        f"正在重试 ({attempt + 1}/{max_attempts})"
                    )
                    await asyncio.sleep(self.server_config.retry_delay)
                else:
                    raise MCPToolCallError(
                        f"工具调用失败: {tool_name} - {e}"
                    ) from e

    async def list_tools(
        self,
        use_cache: bool = True,
        cache_ttl: int = 300
    ) -> List[Dict[str, Any]]:
        """
        获取可用的工具列表。

        Args:
            use_cache: 是否使用缓存
            cache_ttl: 缓存有效期（秒）

        Returns:
            工具列表
        """
        if not self._is_connected:
            await self.connect()

        # 检查缓存
        if use_cache and self._tools_cache is not None:
            if self._cache_timestamp and \
               datetime.now() - self._cache_timestamp < timedelta(seconds=cache_ttl):
                logger.debug("使用缓存的工具列表")
                return self._tools_cache

        try:
            result = await asyncio.wait_for(
                self._session.list_tools(),
                timeout=self.server_config.timeout
            )

            tools = []
            if hasattr(result, "tools"):
                for tool in result.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": getattr(tool, "inputSchema", {})
                    })

            self._tools_cache = tools
            self._cache_timestamp = datetime.now()
            return tools

        except Exception as e:
            raise MCPToolCallError(f"获取工具列表失败: {e}") from e

    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        获取可用的资源列表。

        Returns:
            资源列表
        """
        if not self._is_connected:
            await self.connect()

        try:
            result = await asyncio.wait_for(
                self._session.list_resources(),
                timeout=self.server_config.timeout
            )

            resources = []
            if hasattr(result, "resources"):
                for resource in result.resources:
                    resources.append({
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": getattr(resource, "description", ""),
                        "mimeType": getattr(resource, "mimeType", "")
                    })

            return resources

        except Exception as e:
            raise MCPToolCallError(f"获取资源列表失败: {e}") from e

    async def read_resource(self, uri: str) -> str:
        """
        读取资源内容。

        Args:
            uri: 资源 URI

        Returns:
            资源内容
        """
        if not self._is_connected:
            await self.connect()

        try:
            result = await asyncio.wait_for(
                self._session.read_resource(uri),
                timeout=self.server_config.timeout
            )

            if hasattr(result, "contents") and result.contents:
                content = result.contents[0]
                if hasattr(content, "text"):
                    return content.text

            return str(result)

        except Exception as e:
            raise MCPToolCallError(f"读取资源失败 ({uri}): {e}") from e

    async def list_prompts(self) -> List[Dict[str, Any]]:
        """
        获取可用的提示词模板列表。

        Returns:
            提示词模板列表
        """
        if not self._is_connected:
            await self.connect()

        try:
            result = await asyncio.wait_for(
                self._session.list_prompts(),
                timeout=self.server_config.timeout
            )

            prompts = []
            if hasattr(result, "prompts"):
                for prompt in result.prompts:
                    prompts.append({
                        "name": prompt.name,
                        "description": prompt.description,
                        "arguments": getattr(prompt, "arguments", [])
                    })

            return prompts

        except Exception as e:
            raise MCPToolCallError(f"获取提示词列表失败: {e}") from e

    async def get_prompt(
        self,
        prompt_name: str,
        arguments: Optional[Dict[str, str]] = None
    ) -> str:
        """
        获取提示词内容。

        Args:
            prompt_name: 提示词名称
            arguments: 提示词参数

        Returns:
            提示词内容
        """
        if not self._is_connected:
            await self.connect()

        try:
            result = await asyncio.wait_for(
                self._session.get_prompt(prompt_name, arguments or {}),
                timeout=self.server_config.timeout
            )

            if hasattr(result, "messages") and result.messages:
                messages = result.messages
                if messages and hasattr(messages[0], "content"):
                    content = messages[0].content
                    if hasattr(content, "text"):
                        return content.text

            return str(result)

        except Exception as e:
            raise MCPToolCallError(f"获取提示词失败 ({prompt_name}): {e}") from e

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect()

    def __repr__(self) -> str:
        return (
            f"<MCPClient server_name='{self.server_name}' "
            f"transport={self.server_config.transport_type.value} "
            f"connected={self._is_connected}>"
        )


class MCPClientManager:
    """
    MCP 客户端管理器。

    管理多个 MCP 客户端连接，提供统一的服务器选择和工具调用接口。
    """

    def __init__(self, config: MCPClientConfig):
        """
        初始化 MCP 客户端管理器。

        Args:
            config: MCP 客户端配置
        """
        self.config = config
        self._clients: Dict[str, MCPClient] = {}
        self._default_client: Optional[MCPClient] = None

    async def get_client(self, server_name: Optional[str] = None) -> MCPClient:
        """
        获取指定服务器的客户端。

        Args:
            server_name: 服务器名称，如果为 None 则使用默认服务器

        Returns:
            MCP 客户端实例
        """
        # 确定服务器名称
        if server_name is None:
            server_name = self.config.default_server
            if server_name is None:
                raise MCPClientError(
                    "未指定服务器名称，且没有配置默认服务器"
                )

        # 检查服务器配置是否存在
        if server_name not in self.config.servers:
            raise KeyError(f"未找到服务器配置: {server_name}")

        # 创建或获取客户端
        if server_name not in self._clients:
            server_config = self.config.get_server_config(server_name)
            client = MCPClient(server_config, server_name)
            self._clients[server_name] = client

            # 设置为默认客户端
            if server_name == self.config.default_server:
                self._default_client = client

        return self._clients[server_name]

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None,
        retry: bool = True
    ) -> Any:
        """
        调用指定服务器的工具。

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            server_name: 服务器名称
            retry: 是否重试

        Returns:
            工具执行结果
        """
        client = await self.get_client(server_name)
        return await client.call_tool(tool_name, arguments, retry)

    async def list_tools(
        self,
        server_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取指定服务器的工具列表。

        Args:
            server_name: 服务器名称

        Returns:
            工具列表
        """
        client = await self.get_client(server_name)
        return await client.list_tools(
            use_cache=self.config.enable_caching,
            cache_ttl=self.config.cache_ttl
        )

    async def disconnect_all(self) -> None:
        """断开所有客户端连接"""
        for client in self._clients.values():
            await client.disconnect()
        self._clients.clear()
        logger.info("所有 MCP 客户端已断开连接")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.disconnect_all()
