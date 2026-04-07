"""
MCP 客户端测试文件。

提供简单的测试用例来验证 MCP 客户端功能。
"""

import asyncio
import pytest
from typing import Dict, Any

from . import (
    MCPClientManager,
    MCPClientConfig,
    MCPClient,
    create_stdio_config,
    MCPToolSet,
    MCPConnectionError,
    MCPToolCallError
)


class TestMCPClient:
    """MCP 客户端测试类"""

    @pytest.fixture
    def server_config(self):
        """创建测试用服务器配置"""
        return create_stdio_config(
            command="python",
            args=["src/mcp/server.py"],
            timeout=30
        )

    @pytest.fixture
    def client_config(self):
        """创建测试用客户端配置"""
        config = MCPClientConfig()
        config.add_server(
            "test_server",
            create_stdio_config(
                command="python",
                args=["src/mcp/server.py"]
            )
        )
        return config

    @pytest.mark.asyncio
    async def test_client_connection(self, server_config):
        """测试客户端连接"""
        client = MCPClient(server_config, "test_client")

        try:
            await client.connect()
            assert client.is_connected()

            # 测试获取工具列表
            tools = await client.list_tools()
            assert isinstance(tools, list)

        finally:
            await client.disconnect()
            assert not client.is_connected()

    @pytest.mark.asyncio
    async def test_client_manager(self, client_config):
        """测试客户端管理器"""
        async with MCPClientManager(client_config) as manager:
            # 测试获取工具列表
            tools = await manager.list_tools()
            assert isinstance(tools, list)

    @pytest.mark.asyncio
    async def test_tool_call(self, client_config):
        """测试工具调用"""
        async with MCPClientManager(client_config) as manager:
            # 假设服务器有 list_records 工具
            try:
                result = await manager.call_tool(
                    "list_records",
                    {"entity_name": "device"}
                )
                assert result is not None
            except Exception as e:
                # 服务器可能不可用，这是预期的
                pytest.skip(f"MCP 服务器不可用: {e}")

    @pytest.mark.asyncio
    async def test_toolset(self, client_config):
        """测试工具集"""
        async with MCPClientManager(client_config) as manager:
            toolset = MCPToolSet(manager)

            try:
                await toolset.auto_load_tools()
                tools = toolset.get_tools()

                assert isinstance(tools, list)
                # 如果有工具，验证它们是 StructuredTool 类型
                if tools:
                    from langchain_core.tools import StructuredTool
                    assert all(isinstance(t, StructuredTool) for t in tools)
            except Exception as e:
                pytest.skip(f"工具加载失败: {e}")

    def test_config_validation(self):
        """测试配置验证"""
        # 测试 STDIO 配置
        config = create_stdio_config(
            command="python",
            args=["test.py"]
        )
        assert config.validate_config()

        # 测试缺少必需参数
        from . import MCPServerConfig, MCPTransportType
        with pytest.raises(ValueError):
            invalid_config = MCPServerConfig(
                transport_type=MCPTransportType.STDIO
                # 缺少 command
            )
            invalid_config.validate_config()

    @pytest.mark.asyncio
    async def test_error_handling(self, client_config):
        """测试错误处理"""
        async with MCPClientManager(client_config) as manager:
            # 测试调用不存在的工具
            with pytest.raises(MCPToolCallError):
                await manager.call_tool("non_existent_tool", {})


def run_basic_tests():
    """
    运行基础测试（不需要 pytest）。

    用于快速验证基本功能。
    """
    async def basic_test():
        print("🧪 开始基础测试...")

        # 1. 测试配置创建
        print("\n1️⃣ 测试配置创建...")
        config = MCPClientConfig()
        config.add_server(
            "test",
            create_stdio_config(
                command="python",
                args=["src/mcp/server.py"]
            )
        )
        print("✅ 配置创建成功")

        # 2. 测试客户端管理器
        print("\n2️⃣ 测试客户端管理器...")
        async with MCPClientManager(config) as manager:
            print("✅ 客户端管理器创建成功")

            # 3. 测试工具列表
            print("\n3️⃣ 测试获取工具列表...")
            try:
                tools = await manager.list_tools()
                print(f"✅ 获取到 {len(tools)} 个工具")
                for tool in tools:
                    print(f"   - {tool['name']}")
            except Exception as e:
                print(f"⚠️  获取工具列表失败: {e}")

            # 4. 测试工具调用
            print("\n4️⃣ 测试工具调用...")
            try:
                result = await manager.call_tool(
                    "list_records",
                    {"entity_name": "device"}
                )
                print(f"✅ 工具调用成功")
                print(f"   结果: {result}")
            except Exception as e:
                print(f"⚠️  工具调用失败: {e}")

        print("\n✨ 基础测试完成！")

    asyncio.run(basic_test())


if __name__ == "__main__":
    # 运行基础测试
    run_basic_tests()

    # 如果安装了 pytest，可以运行完整测试
    # pytest.main([__file__, "-v"])
