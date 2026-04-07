"""
MCP 客户端模块。

提供统一的 MCP (Model Context Protocol) 客户端接口，支持：
- 多种传输方式（STDIO、SSE、WebSocket）
- 多服务器管理
- 工具动态加载和调用
- 与 LangChain 无缝集成

使用示例：
```python
from src.agents.mcp_client import (
    MCPClientManager,
    MCPClientConfig,
    create_stdio_config,
    MCPToolSet
)

# 创建配置
config = MCPClientConfig()
config.add_server("local", create_stdio_config(
    command="python",
    args=["src/mcp/server.py"]
))

# 创建客户端管理器
manager = MCPClientManager(config)

# 创建工具集
toolset = MCPToolSet(manager)
await toolset.auto_load_tools()

# 获取工具
tools = toolset.get_tools()

# 调用工具
result = await manager.call_tool("tool_name", {"param": "value"})
```
"""

from .client import MCPClient, MCPClientManager
from .config import (
    MCPServerConfig,
    MCPClientConfig,
    MCPTransportType,
    create_stdio_config,
    create_sse_config
)
from .tools import MCPToolFactory, MCPToolSet
from .exceptions import (
    MCPClientError,
    MCPConnectionError,
    MCPToolCallError,
    MCPInitializationError,
    MCPTimeoutError
)

__version__ = "0.1.0"

__all__ = [
    # 核心客户端
    "MCPClient",
    "MCPClientManager",

    # 配置
    "MCPServerConfig",
    "MCPClientConfig",
    "MCPTransportType",
    "create_stdio_config",
    "create_sse_config",

    # 工具集成
    "MCPToolFactory",
    "MCPToolSet",

    # 异常
    "MCPClientError",
    "MCPConnectionError",
    "MCPToolCallError",
    "MCPInitializationError",
    "MCPTimeoutError",
]
