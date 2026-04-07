# MCP 客户端

统一的 MCP (Model Context Protocol) 客户端接口，支持多种传输方式和服务器管理。

## 功能特性

- ✅ **多传输协议支持**: STDIO、SSE、WebSocket
- ✅ **多服务器管理**: 同时连接和管理多个 MCP 服务器
- ✅ **工具动态加载**: 自动从服务器加载工具列表和 Schema
- ✅ **LangChain 集成**: 无缝集成到 LangChain Agent 框架
- ✅ **异步支持**: 完全异步的 API 设计
- ✅ **错误处理**: 完善的异常处理和重试机制
- ✅ **类型提示**: 完整的类型注解
- ✅ **连接管理**: 自动连接管理和上下文管理器

## 安装依赖

```bash
pip install mcp
pip install pydantic pydantic-settings
pip install langchain-core
```

## 快速开始

### 1. 基本使用

```python
import asyncio
from src.agents.mcp_client import (
    MCPClientManager,
    MCPClientConfig,
    create_stdio_config
)

async def main():
    # 创建配置
    config = MCPClientConfig()
    config.add_server("local", create_stdio_config(
        command="python",
        args=["src/mcp/server.py"]
    ))

    # 使用客户端
    async with MCPClientManager(config) as manager:
        # 调用工具
        result = await manager.call_tool(
            "tool_name",
            {"param": "value"}
        )
        print(result)

asyncio.run(main())
```

### 2. LangChain 集成

```python
from src.agents.mcp_client import MCPClientManager, MCPClientConfig, MCPToolSet
from langchain.agents import create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

async def main():
    # 配置 MCP 客户端
    config = MCPClientConfig()
    config.add_server("local", create_stdio_config(
        command="python",
        args=["src/mcp/server.py"]
    ))

    async with MCPClientManager(config) as manager:
        # 创建工具集并加载工具
        toolset = MCPToolSet(manager)
        await toolset.auto_load_tools()

        # 获取 LangChain 兼容的工具
        tools = toolset.get_tools()

        # 创建 Agent
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)

        # 使用 Agent
        response = await agent.ainvoke({
            "input": "使用 MCP 工具完成任务"
        })
```

### 3. 多服务器管理

```python
async def main():
    config = MCPClientConfig()

    # 添加多个服务器
    config.add_server("server1", create_stdio_config(
        command="python",
        args=["server1.py"]
    ))

    config.add_server("server2", create_stdio_config(
        command="python",
        args=["server2.py"]
    ))

    async with MCPClientManager(config) as manager:
        # 从不同服务器调用工具
        result1 = await manager.call_tool(
            "tool1", {},
            server_name="server1"
        )

        result2 = await manager.call_tool(
            "tool2", {},
            server_name="server2"
        )
```

## API 参考

### MCPClientManager

客户端管理器，负责管理多个 MCP 客户端连接。

#### 方法

- `get_client(server_name: Optional[str] = None) -> MCPClient`: 获取客户端实例
- `call_tool(tool_name, arguments, server_name=None, retry=True)`: 调用工具
- `list_tools(server_name=None) -> List[Dict]`: 获取工具列表
- `disconnect_all()`: 断开所有连接

### MCPClient

单个 MCP 服务器客户端。

#### 方法

- `connect()`: 连接到服务器
- `disconnect()`: 断开连接
- `call_tool(tool_name, arguments, retry=True)`: 调用工具
- `list_tools(use_cache=True, cache_ttl=300)`: 获取工具列表
- `list_resources()`: 获取资源列表
- `read_resource(uri)`: 读取资源
- `list_prompts()`: 获取提示词列表
- `get_prompt(name, arguments)`: 获取提示词内容

### MCPToolSet

工具集管理器，用于创建和管理 LangChain 兼容的工具。

#### 方法

- `load_tools(server_name=None, server_names=None)`: 加载工具
- `get_tools(server_name=None) -> List[StructuredTool]`: 获取工具
- `get_tool_by_name(tool_name, server_name=None)`: 获取指定工具
- `list_tools(server_name=None) -> List[str]`: 列出工具名称
- `auto_load_tools()`: 自动加载所有工具

## 配置说明

### MCPServerConfig

服务器配置类。

#### 参数

- `transport_type`: 传输类型 (stdio/sse/websocket)
- `command`: STDIO 模式下的启动命令
- `args`: 命令参数列表
- `env`: 环境变量字典
- `url`: SSE/WebSocket 模式下的 URL
- `timeout`: 连接超时时间（秒）
- `max_retries`: 最大重试次数
- `retry_delay`: 重试延迟（秒）
- `headers`: HTTP 请求头

### MCPClientConfig

客户端总配置。

#### 参数

- `servers`: 服务器配置字典
- `default_server`: 默认服务器名称
- `enable_caching`: 是否启用缓存
- `cache_ttl`: 缓存有效期（秒）
- `log_level`: 日志级别

## 异常处理

```python
from src.agents.mcp_client import (
    MCPConnectionError,
    MCPToolCallError,
    MCPTimeoutError,
    MCPInitializationError
)

try:
    result = await manager.call_tool("tool", {})
except MCPConnectionError as e:
    print(f"连接失败: {e}")
except MCPToolCallError as e:
    print(f"工具调用失败: {e}")
except MCPTimeoutError as e:
    print(f"操作超时: {e}")
```

## 高级用法

### 自定义重试策略

```python
config = create_stdio_config(
    command="python",
    args=["server.py"],
    timeout=10,      # 10秒超时
    max_retries=5,   # 最多重试5次
    retry_delay=2.0  # 每次重试间隔2秒
)
```

### 禁用缓存

```python
config = MCPClientConfig(
    enable_caching=False,
    cache_ttl=0
)
```

### 直接使用客户端

```python
from src.agents.mcp_client import MCPClient

client = MCPClient(server_config, "my_client")

try:
    await client.connect()
    result = await client.call_tool("tool", {})
finally:
    await client.disconnect()
```

## 注意事项

1. **异步操作**: 所有方法都是异步的，需要在异步上下文中调用
2. **连接管理**: 使用上下文管理器确保连接正确关闭
3. **错误处理**: 建议捕获和处理各种异常
4. **超时设置**: 根据实际情况调整超时时间
5. **缓存策略**: 工具列表会被缓存，注意缓存有效期

## 示例代码

更多示例请参考 [examples.py](examples.py) 文件。

## 相关文档

- [MCP 协议规范](https://modelcontextprotocol.io/)
- [LangChain 文档](https://python.langchain.com/)
- [项目主文档](../../README.md)
