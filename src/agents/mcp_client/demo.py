"""
MCP 客户端快速演示脚本。

展示如何在现有项目中使用 MCP 客户端。
"""

import asyncio
import logging
from pathlib import Path

# 添加项目根目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.mcp_client import (
    MCPClientManager,
    MCPClientConfig,
    MCPToolSet,
    create_stdio_config
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_quick_start():
    """快速开始演示"""
    print("\n" + "="*60)
    print("MCP 客户端快速开始演示")
    print("="*60)

    # 1. 创建配置
    print("\n📝 步骤 1: 创建 MCP 客户端配置")
    config = MCPClientConfig()

    # 添加本地 MCP 服务器配置
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
    print("✅ 配置创建完成")

    # 2. 创建客户端管理器
    print("\n📝 步骤 2: 创建客户端管理器")
    async with MCPClientManager(config) as manager:
        print("✅ 客户端管理器创建成功")

        # 3. 获取可用工具列表
        print("\n📝 步骤 3: 获取可用工具列表")
        try:
            tools = await manager.list_tools()
            print(f"✅ 发现 {len(tools)} 个可用工具:")
            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool['name']}")
                print(f"      描述: {tool['description']}")
        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")
            print("⚠️  无法连接到 MCP 服务器，请确保服务器正在运行")
            return

        # 4. 演示工具调用
        print("\n📝 步骤 4: 演示工具调用")
        try:
            # 调用 list_records 工具
            result = await manager.call_tool(
                "list_records",
                {"entity_name": "device"}
            )
            print("✅ 工具调用成功:")
            print(f"   结果: {result}")
        except Exception as e:
            logger.error(f"工具调用失败: {e}")

    print("\n✨ 演示完成！")


async def demo_langchain_integration():
    """LangChain 集成演示"""
    print("\n" + "="*60)
    print("LangChain 集成演示")
    print("="*60)

    # 创建配置
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
        print("\n📝 创建 MCP 工具集")
        toolset = MCPToolSet(manager)

        try:
            # 自动加载工具
            await toolset.auto_load_tools()
            print("✅ 工具加载完成")

            # 获取工具列表
            tools = toolset.get_tools()
            print(f"\n📝 已加载 {len(tools)} 个 LangChain 工具:")

            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool.name}")
                print(f"      描述: {tool.description}")

            print("\n💡 这些工具可以直接用于 LangChain Agent:")
            print("   from langchain.agents import create_tool_calling_agent")
            print("   agent = create_tool_calling_agent(llm, tools, prompt)")

        except Exception as e:
            logger.error(f"工具加载失败: {e}")
            print("⚠️  无法加载工具，请确保 MCP 服务器正在运行")


async def demo_domain_agent_integration():
    """领域 Agent 集成演示"""
    print("\n" + "="*60)
    print("领域 Agent 集成演示")
    print("="*60)

    from src.agents.core.domain_agent import DomainAgent
    from langchain_core.tools import tool

    # 创建一个使用 MCP 工具的领域 Agent
    print("\n📝 创建集成 MCP 工具的领域 Agent")

    class MyMCPAgent(DomainAgent):
        """使用 MCP 工具的领域 Agent 示例"""

        def __init__(self):
            super().__init__(
                name="mcp_demo_agent",
                description="演示如何集成 MCP 工具的领域 Agent"
            )
            self._mcp_tools = []

        async def _load_mcp_tools(self):
            """加载 MCP 工具"""
            config = MCPClientConfig()
            config.add_server(
                "local_mcp",
                create_stdio_config(
                    command="python",
                    args=["src/mcp/server.py"]
                )
            )

            async with MCPClientManager(config) as manager:
                toolset = MCPToolSet(manager)
                await toolset.auto_load_tools()
                self._mcp_tools = toolset.get_tools()

        async def get_tools(self):
            """获取工具列表"""
            if not self._mcp_tools:
                await self._load_mcp_tools()
            return self._mcp_tools

        def get_system_prompt(self):
            return """你是一个使用 MCP 工具的演示 Agent。

你可以访问以下 MCP 工具来完成任务：
- 查询设备状态
- 管理设备记录
- 执行设备操作

请根据用户需求选择合适的工具。
"""

    try:
        # 创建 Agent 实例
        agent = MyMCPAgent()

        # 获取工具
        tools = await agent.get_tools()

        print(f"✅ Agent 创建成功，包含 {len(tools)} 个 MCP 工具")
        print(f"   Agent 名称: {agent.name}")
        print(f"   Agent 描述: {agent.description}")

        # 转换为 SubAgent 配置
        subagent_config = agent.to_subagent_config()
        print(f"✅ SubAgent 配置生成成功")
        print(f"   工具数量: {len(subagent_config['tools'])}")

    except Exception as e:
        logger.error(f"Agent 创建失败: {e}")
        print("⚠️  无法创建 Agent，请确保 MCP 服务器正在运行")


async def main():
    """运行所有演示"""
    print("\n" + "="*60)
    print("MCP 客户端演示程序")
    print("="*60)
    print("\n本程序演示如何在项目中使用 MCP 客户端")

    try:
        # 演示 1: 快速开始
        await demo_quick_start()

        # 演示 2: LangChain 集成
        await demo_langchain_integration()

        # 演示 3: 领域 Agent 集成
        await demo_domain_agent_integration()

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断演示")
    except Exception as e:
        logger.exception(f"演示执行出错: {e}")

    print("\n" + "="*60)
    print("演示程序结束")
    print("="*60)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
