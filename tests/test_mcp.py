"""
MCP 服务测试脚本

用于验证 MCP 服务是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 设置 UTF-8 编码输出（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("❌ 缺少依赖，请先安装：")
    print("   pip install mcp")
    sys.exit(1)


async def test_mcp_connection():
    """测试 MCP 服务连接和工具调用"""

    print("=" * 60)
    print("EMS MCP 服务测试")
    print("=" * 60)

    # 配置服务器参数
    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp/server.py"],
        env={"API_BASE_URL": "http://localhost:8000"}
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化
                print("\n📡 正在连接 MCP 服务...")
                await session.initialize()
                print("✅ 连接成功！\n")

                # 获取可用工具
                tools = await session.list_tools()
                print(f"📋 发现 {len(tools.tools)} 个可用工具：")
                for tool in tools.tools:
                    print(f"   • {tool.name}: {tool.description[:50]}...")
                print()

                # 测试 1: 列出可管理实体
                print("=" * 60)
                print("测试 1: 列出可管理实体")
                print("=" * 60)
                result = await session.call_tool("list_manageable_entities", {})
                print(result.content[0].text)
                print()

                # 测试 2: 获取设备字段
                print("=" * 60)
                print("测试 2: 获取设备字段定义")
                print("=" * 60)
                result = await session.call_tool("get_entity_fields", {
                    "entity_name": "device"
                })
                print(result.content[0].text)
                print()

                # 测试 3: 查询记录列表
                print("=" * 60)
                print("测试 3: 查询设备列表")
                print("=" * 60)
                result = await session.call_tool("list_records", {
                    "entity_name": "device"
                })
                print(result.content[0].text)
                print()

                # 测试 4: 创建记录（模拟）
                print("=" * 60)
                print("测试 4: 创建新设备（模拟）")
                print("=" * 60)
                result = await session.call_tool("create_record", {
                    "entity_name": "device",
                    "record_data": {
                        "name": "测试电池组",
                        "type": "BATTERY",
                        "location": "测试实验室",
                        "metadata": {"capacity": 100}
                    }
                })
                print(result.content[0].text)
                print()

                print("=" * 60)
                print("✅ 所有测试完成！")
                print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


async def interactive_mode():
    """交互式测试模式"""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp/server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("\n🎯 交互式模式（输入 'quit' 退出）")
            print("可用命令：")
            print("  list                    - 列出可管理实体")
            print("  fields <entity>         - 获取实体字段")
            print("  list_records <entity>   - 查询记录列表")
            print("  help                    - 显示帮助\n")

            while True:
                try:
                    cmd = input("mcp> ").strip().split()
                    if not cmd:
                        continue
                    if cmd[0] == "quit":
                        break

                    if cmd[0] == "list":
                        result = await session.call_tool("list_manageable_entities", {})
                        print(result.content[0].text)

                    elif cmd[0] == "fields" and len(cmd) > 1:
                        result = await session.call_tool("get_entity_fields", {
                            "entity_name": cmd[1]
                        })
                        print(result.content[0].text)

                    elif cmd[0] == "list_records" and len(cmd) > 1:
                        result = await session.call_tool("list_records", {
                            "entity_name": cmd[1]
                        })
                        print(result.content[0].text)

                    elif cmd[0] == "help":
                        print("可用命令：")
                        print("  list                    - 列出可管理实体")
                        print("  fields <entity>         - 获取实体字段")
                        print("  list_records <entity>   - 查询记录列表")
                        print("  quit                    - 退出")

                    else:
                        print("❌ 未知命令，输入 'help' 查看帮助")

                except KeyboardInterrupt:
                    print("\n👋 再见！")
                    break
                except Exception as e:
                    print(f"❌ 错误: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试 EMS MCP 服务")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="进入交互式模式"
    )

    args = parser.parse_args()

    if args.interactive:
        asyncio.run(interactive_mode())
    else:
        success = asyncio.run(test_mcp_connection())
        sys.exit(0 if success else 1)
