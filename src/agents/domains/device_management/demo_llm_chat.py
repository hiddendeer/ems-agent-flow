"""
设备管理智能体 — 增强版测试脚本 (显示内部工具调用)
修复: F-string 不允许包含反斜杠错误
"""

import asyncio
from src.agents.core.factory import create_ems_agent
from src.agents.domains import register_all_domains

register_all_domains()

async def interactive_test():
    agent = create_ems_agent()
    
    print(f"\n============================================================")
    print("🤖 EMS 业务-AI 融合逻辑全流程实测")
    print("场景模拟: BESS_01 已存在 -> AI 尝试重命名 -> 补全容量 -> 自动提示配网")
    print(f"============================================================\n")

    test_queries = [
        "帮我录入一个叫 BESS_01 的新设备",
        "既然 BESS_01 已经有了，那叫 BESS_NEW_2026 吧，它是个储能电池",
        "它的额定容量是 2000kWh",
    ]

    history = []
    for query in test_queries:
        print(f"👤 [用户]: {query}")
        history.append(("user", query))
        
        response_text = ""
        # 运行 Agent 流
        async for step in agent.astream({"messages": history}):
            if not isinstance(step, dict): continue
            
            for node, values in step.items():
                if isinstance(values, dict) and "messages" in values:
                    msgs_raw = values.get("messages", [])
                    msgs = getattr(msgs_raw, "value", msgs_raw) if not isinstance(msgs_raw, list) else msgs_raw
                    
                    for msg in msgs:
                        msg_type = msg.__class__.__name__
                        if msg_type == 'AIMessage' and hasattr(msg, 'tool_calls') and msg.tool_calls:
                            for tc in msg.tool_calls:
                                print(f"   🔧 [Executing Tool]: {tc['name']}")
                        
                        if msg_type == 'ToolMessage':
                            # 截取前 100 字符，并移除换行符
                            clean_content = msg.content[:100].replace('\n', ' ')
                            print(f"   📤 [Tool Response]: {clean_content}...")

                        if msg_type == 'AIMessage' and msg.content:
                            response_text = msg.content

        if response_text:
            clean_ai_resp = response_text.replace('\n', ' ')
            print(f"🤖 [AI]: {clean_ai_resp}\n")
            history.append(("assistant", response_text))
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(interactive_test())
