"""
MCP 客户端使用示例。

展示如何使用 MCP 客户端连接到 MCP 服务器并调用工具。
"""

import asyncio
import logging
from typing import Dict, Any

from . import (
    MCPClientManager,
    MCPClientConfig,
    create_stdio_config,
    MCPToolSet
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """
    基本使用示例。

    展示如何：
    1. 创建配置
    2. 连接到 MCP 服务器
    3. 调用工具
    4. 断开连接
    """
    print("\n" + "="*50)
    print("示例 1: 基本使用")
    print("="*50)

    # 1. 创建配置
    config = MCPClientConfig()

    # 添加 STDIO 类型的服务器配置
    config.add_server(
        "local_mcp",
        create_stdio_config(
            command="python",
            args=["src/mcp/server.py"],
            env={"API_BASE_URL": "http://localhost:8000"},
            timeout=30
        )
    )

    config.default_server = "local_mcp"

    # 2. 创建客户端管理器
    async with MCPClientManager(config) as manager:
        try:
            # 3. 列出可用工具
            tools = await manager.list_tools()
            print(f"\n✅ 可用工具 ({len(tools)} 个):")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")

            # 4. 调用工具示例
            print(f"\n📞 调用工具示例:")

            # 示例：列出记录
            result = await manager.call_tool(
                "list_records",
                {"entity_name": "device"}
            )
            print(f"  list_records 结果: {result}")

        except Exception as e:
            logger.error(f"执行失败: {e}")


async def example_multiple_servers():
    """
    多服务器示例。

    展示如何同时连接多个 MCP 服务器。
    """
    print("\n" + "="*50)
    print("示例 2: 多服务器管理")
    print("="*50)

    config = MCPClientConfig()

    # 添加多个服务器
    config.add_server(
        "server1",
        create_stdio_config(
            command="python",
            args=["src/mcp/server.py"]
        )
    )

    config.add_server(
        "server2",
        create_stdio_config(
            command="python",
            args=["src/mcp/server.py"]  # 实际使用时应该是不同的服务器
        )
    )

    config.default_server = "server1"

    async with MCPClientManager(config) as manager:
        # 从不同服务器调用工具
        try:
            result1 = await manager.call_tool(
                "list_records",
                {"entity_name": "device"},
                server_name="server1"
            )
            print(f"  Server1 结果: {result1}")

            result2 = await manager.call_tool(
                "list_records",
                {"entity_name": "device"},
                server_name="server2"
            )
            print(f"  Server2 结果: {result2}")

        except Exception as e:
            logger.error(f"多服务器调用失败: {e}")


async def example_langchain_integration():
    """
    LangChain 集成示例。

    展示如何将 MCP 工具集成到 LangChain Agent 中使用。
    """
    print("\n" + "="*50)
    print("示例 3: LangChain 集成")
    print("="*50)

    config = MCPClientConfig()

    config.add_server(
        "local_mcp",
        create_stdio_config(
            command="python",
            args=["src/mcp/server.py"]
        )
    )

    async with MCPClientManager(config) as manager:
        # 创建工具集
        toolset = MCPToolSet(manager)

        # 自动加载所有工具
        await toolset.auto_load_tools()

        # 获取 LangChain 兼容的工具
        tools = toolset.get_tools()

        print(f"\n✅ 已加载 {len(tools)} 个 LangChain 工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # 演示：直接使用工具
        if tools:
            sample_tool = tools[0]
            print(f"\n📞 演示调用工具: {sample_tool.name}")

            # 注意：实际调用需要根据工具的参数要求
            try:
                # 这里只是示例，实际参数需要根据工具要求
                result = await sample_tool.ainvoke({})
                print(f"  结果: {result}")
            except Exception as e:
                print(f"  调用失败（可能需要参数）: {e}")

        # 这些工具可以直接传递给 LangChain Agent
        print(f"\n💡 提示: 这些工具可以直接用于 LangChain Agent:")
        print(f"  agent = create_tool_calling_agent(llm, tools, prompt)")


async def example_direct_client_usage():
    """
    直接使用客户端示例。

    展示如何直接使用 MCPClient 类。
    """
    print("\n" + "="*50)
    print("示例 4: 直接使用客户端")
    print("="*50)

    from . import MCPClient

    # 创建客户端配置
    server_config = create_stdio_config(
        command="python",
        args=["src/mcp/server.py"]
    )

    # 创建客户端
    client = MCPClient(server_config, "my_client")

    try:
        # 连接
        await client.connect()
        print(f"✅ 已连接到 MCP 服务器")

        # 列出工具
        tools = await client.list_tools()
        print(f"📋 可用工具: {[t['name'] for t in tools]}")

        # 列出资源
        resources = await client.list_resources()
        print(f"📚 可用资源: {[r['name'] for r in resources]}")

        # 调用工具
        result = await client.call_tool(
            "list_records",
            {"entity_name": "device"}
        )
        print(f"📞 调用结果: {result}")

    finally:
        # 断开连接
        await client.disconnect()
        print(f"🔌 已断开连接")


async def example_error_handling():
    """
    错误处理示例。

    展示如何处理各种异常情况。
    """
    print("\n" + "="*50)
    print("示例 5: 错误处理")
    print("="*50)

    from . import (
        MCPConnectionError,
        MCPToolCallError,
        MCPTimeoutError
    )

    config = MCPClientConfig()

    # 添加一个可能失败的服务器配置
    config.add_server(
        "invalid_server",
        create_stdio_config(
            command="python",
            args=["non_existent_server.py"],
            timeout=5  # 短超时
        )
    )

    async with MCPClientManager(config) as manager:
        try:
            # 尝试调用不存在的工具
            result = await manager.call_tool(
                "non_existent_tool",
                {},
                server_name="invalid_server"
            )
        except MCPConnectionError as e:
            print(f"❌ 连接错误: {e}")
        except MCPToolCallError as e:
            print(f"❌ 工具调用错误: {e}")
        except MCPTimeoutError as e:
            print(f"❌ 超时错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")


async def main():
    """
    运行所有示例。
    """
    print("\n" + "="*50)
    print("MCP 客户端使用示例")
    print("="*50)

    # 运行示例
    try:
        await example_basic_usage()
    except Exception as e:
        logger.error(f"示例 1 执行失败: {e}")

    try:
        await example_multiple_servers()
    except Exception as e:
        logger.error(f"示例 2 执行失败: {e}")

    try:
        await example_langchain_integration()
    except Exception as e:
        logger.error(f"示例 3 执行失败: {e}")

    try:
        await example_direct_client_usage()
    except Exception as e:
        logger.error(f"示例 4 执行失败: {e}")

    try:
        await example_error_handling()
    except Exception as e:
        logger.error(f"示例 5 执行失败: {e}")

    print("\n" + "="*50)
    print("所有示例执行完毕")
    print("="*50)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
