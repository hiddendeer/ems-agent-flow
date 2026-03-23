import asyncio
from src.agents.core.factory import agent_factory

async def test():
    agent = agent_factory(system_prompt="You are a helpful assistant.")
    print("Agent created. Invoking...")
    async for step in agent.astream({"messages": [("user", "Hello, who are you?")]}):
        print(f"Step: {step}")

if __name__ == "__main__":
    asyncio.run(test())
