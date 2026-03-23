import asyncio
from ..core.factory import agent_factory
from ..tools.system_tools import get_system_info

async def run_simple_demo():
    """
    演示简单的 Deep Agent 的创建与调用逻辑。
    Deep Agent 默认集成了规划 (write_todos)、文件操作 (ls, read_file 等) 和 执行 (execute) 工具。
    """
    
    # 注入系统提示词
    system_prompt = "You are a helpful system administrator assistant. You can access system info and perform file operations."
    
    # 创建 agent 实例，传入自定义工具
    # 也可以在 settings.py 中设置 DEFAULT_MODEL 为 deepseek:deepseek-chat 等
    agent = agent_factory(
        system_prompt=system_prompt,
        tools=[get_system_info],
        name="SysAdminAgent"
    )
    
    # 待解决的问题
    query = "请先获取该系统的系统信息。然后在项目的 src/agents 目录下新建一个 readme.md 文件，简单描述一下该目前已有的目录结构 (config, core, tools, demo)。直接写入该文件，不要使用 ls 进行全项目扫描。"
    
    print(f"\n--- [DEMO] Query: {query} ---\n")
    
    # 执行流程：
    # 1. 它可以规划步骤 (write_todos)
    # 2. 调用 get_system_info 获取系统信息
    # 3. 使用 write_file 工具在路径下建 readme.md
    
    try:
        # 实时打印执行过程
        print("开始工作...\n")
        async for step in agent.astream({"messages": [("user", query)]}):
            # 如果是工具调用
            if "tools" in step:
                print(f"\n[Tool Call] {step['tools']}")
            # 如果是模型回复
            elif "model" in step:
                msg = step['model']['messages'][-1]
                print(f"\n[Agent] {msg.content}")
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    print(f"--- Tool Calls: {msg.tool_calls}")
    except Exception as e:
        print(f"\n[Error] 执行失败: {e}")
        print("请检查是否已在 .env 中设置相应的 LLM API_KEY (如 ANTHROPIC_API_KEY)。")

if __name__ == "__main__":
    asyncio.run(run_simple_demo())
