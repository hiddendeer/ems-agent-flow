import asyncio
from src.agents.core.factory import agent_factory
from src.agents.tools.system_tools import get_system_info

async def test_tool_calling():
    agent = agent_factory(tools=[get_system_info])
    print("Agent created. Invoking with tool request...")
    # Just ask for system info, which requires get_system_info
    query = "请使用 get_system_info 工具获取系统信息并告诉我。"
    async for step in agent.astream({"messages": [("user", query)]}):
        print(f"STEP KEYS: {list(step.keys())}")
        if "model" in step:
            msg = step["model"]["messages"][-1]
            print(f"Agent content: {msg.content}")
            if hasattr(msg, "tool_calls"):
                print(f"Tool calls: {msg.tool_calls}")
        if "tools" in step:
            print(f"Tool results: {step['tools']}")

if __name__ == "__main__":
    asyncio.run(test_tool_calling())
