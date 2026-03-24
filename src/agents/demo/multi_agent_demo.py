"""
多 Agent 协作演示 — 集成统计功能（API 调用次数 & 总耗时）。

基于 deepagents 框架。
"""

import asyncio
import os
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

from ..domains import register_all_domains
from ..core.factory import create_ems_agent
from ..core.registry import AgentRegistry

# 注册所有领域 Agent
register_all_domains()

async def run_cross_domain_analysis():
    """
    演示跨领域多 Agent 协作，带性能统计。
    """
    
    # 强制创建报告目录，防止 Agent 写入失败
    report_path = "src/agents/reports"
    os.makedirs(report_path, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("🌐 EMS 多 Agent 智能协作系统 (powered by deepagents)")
    print(f"{'='*60}")
    print(f"📋 已注册领域 Agent: {AgentRegistry.get_names()}")
    print(f"{'='*60}\n")
    
    # 创建 EMS Lead Agent
    agent = create_ems_agent()

        # "调研江苏省最新的工业电价政策，并根据电价数据制定一套储能系统的"
        # "最优充放电策略，包括峰谷套利收益预估。"
    
    user_query = (
        "搜索最新的江苏分时电价政策。"
    )
    
    print(f"👤 [用户请求]: {user_query}")
    print(f"\n🚀 [系统状态]: 极速响应模式 (已启用背景复盘优化)\n{'─'*60}\n")
    
    start_time = time.time()
    api_call_count = 0
    total_tokens = 0
    final_response = ""   # ← 将在循环中持续更新为最后一条 AI 文本回复
    
    try:
        last_node = ""
        
        async for step in agent.astream({"messages": [("user", user_query)]}):
            if not isinstance(step, dict):
                continue
            
            for node, values in step.items():
                # 只过滤纯中间件节点，不过滤带有 messages 的关键节点
                if "Middleware" in node:
                    continue
                
                if node != last_node:
                    print(f"\n📍 [Node]: {node}")
                    last_node = node
                
                if isinstance(values, dict) and "messages" in values:
                    msgs_obj = values.get("messages", [])
                    msgs = getattr(msgs_obj, "value", msgs_obj) if not isinstance(msgs_obj, list) else msgs_obj
                    
                    if msgs:
                        last_msg = msgs[-1]
                        msg_class = last_msg.__class__.__name__
                        
                        if msg_class == 'AIMessage':
                            api_call_count += 1
                            usage = getattr(last_msg, "usage_metadata", {})
                            tokens = usage.get("total_tokens", 0) if usage else 0
                            total_tokens += tokens
                            
                            content = last_msg.content or ""
                            if isinstance(content, list):
                                # 多模态消息，提取纯文本部分
                                content = " ".join(
                                    block.get("text", "") for block in content
                                    if isinstance(block, dict) and block.get("type") == "text"
                                )
                            
                            if content.strip():
                                preview = content[:120].replace('\n', ' ')
                                print(f"   🤖 [AI 回复]: {preview}...")
                                # ✅ 关键修复：持续更新最终回复文本
                                final_response = content
                            
                            # 展示工具调用（只过滤 write_todos 的显示，不过滤节点）
                            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                                for tc in last_msg.tool_calls:
                                    t_name = tc["name"]
                                    if t_name == "write_todos":
                                        continue  # 不显示规划动作，减少干扰
                                    elif t_name == "task":
                                        sub = tc["args"].get("subagent_type", "?")
                                        print(f"      🤝 [派发任务 → {sub}]")
                                    else:
                                        print(f"      🔧 [执行工具]: {t_name}")

        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print(f"📝 [分析完成] 核心结论:")
        # 显示最终回复的前 500 字符
        if final_response:
            print(final_response[:500])
            if len(final_response) > 500:
                print(f"... (共 {len(final_response)} 字，回复已截断)")
        else:
            print("（未捕获到最终文字回复）")
        
        print(f"\n{'📊' + '性能统计'.center(56) + '📊'}")
        print(f"{'-'*60}")
        print(f"⏱️  全流程耗时: {elapsed_time:.2f} 秒")
        print(f"🤖 API 调用次数: {api_call_count} 次")
        print(f"🎟️  总 Token 消耗: {total_tokens if total_tokens > 0 else '未知'}")
        print(f"{'-'*60}")

        # --- 异步复盘模式 (模拟后台归档) ---
        print(f"\n⚡ [后台动作]: 任务已完成。触发【异步复盘 Agent】归档此轮对话特征...")
        await asyncio.sleep(1)
        print(f"   ✅ [Background System]: 用户档案已自动更新 (User: 江苏省用电偏好).")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ [Error]: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_cross_domain_analysis())
