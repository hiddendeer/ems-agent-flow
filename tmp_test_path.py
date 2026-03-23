import asyncio
import os
from src.agents.core.factory import agent_factory

async def test_path():
    agent = agent_factory(system_prompt="You are a file manager assistant. Always use relative paths starting with 'src/agents/demo/reports/'.")
    query = "请在 'src/agents/demo/reports/test_verify.txt' 文件中写入 'Path Verification Successful'。"
    
    print(f"Current Working Directory: {os.getcwd()}")
    async for step in agent.astream({"messages": [("user", query)]}):
        print(step.keys())

if __name__ == "__main__":
    asyncio.run(test_path())
