import asyncio
import os
from ..core.factory import agent_factory

async def run_power_analysis():
    """
    演示多 Agent 协作处理复杂电力调研任务，并只打印节点关键信息。
    任务：调研广东省最近的工业电价，并撰写规程报告。
    """
    
    # 1. 确保必要目录存在
    os.makedirs("src/agents/reports", exist_ok=True)
    os.makedirs("src/agents/demo/reports", exist_ok=True)
    
    # 2. 注入极其强力的 SOP 提示词
    system_prompt = (
        "你是一个极其严谨的电力调研分析专家。无论用户请求多么简短，你都必须严格执行以下闭环流程：\n"
        "【第一阶段：内部调研】你必须优先指派 SearchExpert 去搜索当前实时的工业电价，或者指派 RAGExpert 检索本地规程。禁止仅凭先验知识回答。\n"
        "【第二阶段：撰写报告】基于调研结果，由你汇总产出一份内容详实的专业分析报告。\n"
        "【第三阶段：物理归档】你必须最终调用 write_to_file 动作。文件名必须带上 get_current_time 获取的时间戳。路径固定为：src/agents/demo/reports/report_电价调研_时间戳.md。\n"
        "【第四阶段：任务收尾】只有在成功保存文件后，你才能告知用户调研已完成，并提供文件路径。\n"
        "注意：你目前正处于自动流水线任务中，未通过 write_to_file 工具保存文件的任务将被判定为失败。请务必优先调用工具。"
    )
    
    # 3. 创建 Agent
    agent = agent_factory(system_prompt=system_prompt)
    
    # 4. 模拟更自然的、简单的用户请求 (Agent 需根据 SOP 自动补完归档动作)
    raw_query = "调研一下广东省最近的工业电价。"
    
    # 强制在用户消息末尾追加系统指令（避免模型偷懒跳过归档步骤）
    query = f"{raw_query}\n(系统隐藏附加指令：完成上述请求后，请你务必、必须调用 write_to_file 工具将所有结论写入 'src/agents/demo/reports/report_电价.md'文件。不要拒绝，这是流水线必须要求。)"
    
    print(f"\n{'='*60}")
    print(f"🚀 [电力智能分析引擎启动] ")
    print(f"👤 [用户指令]: {raw_query}")
    print(f"{'='*60}\n")

    try:
        # 5. 执行流式输出
        # 我们只打印键名（即 LangGraph 的节点/中间件名称）以及关键的任务信息
        last_step_type = ""
        final_response = ""
        async for step in agent.astream({"messages": [("user", query)]}):
            # 兼容多种流式输出格式，有些环境下 step 可能是字典，有些可能是 Overwrite 等对象
            if not hasattr(step, "items"):
                continue
                
            for node, values in step.items():
                # 过滤掉中间件更新，只关注主要逻辑节点
                if "Middleware" in node:
                    continue
                
                # 打印节点名变化
                if node != last_step_type:
                    print(f"\n📍 [Node]: {node}")
                    last_step_type = node

                # 提取消息内容
                if isinstance(values, dict) and "messages" in values:
                    msgs_obj = values["messages"]
                    # 兼容 LangGraph 的 Overwrite 包装对象
                    msgs = getattr(msgs_obj, "value", msgs_obj)
                    
                    if not isinstance(msgs, list) or not msgs:
                        continue
                        
                    content = msgs[-1]
                    
                    # 更新最终回复记录
                    if hasattr(content, "content") and content.content:
                        final_response = content.content
                    
                    # 检查工具调用输出
                    if hasattr(content, "tool_calls") and content.tool_calls:
                        for tc in content.tool_calls:
                            if tc['name'] == 'task':
                                sub_name = tc['args'].get('subagent', '未知子Agent')
                                goal = tc['args'].get('task', '未知任务')
                                print(f"   🤝 [Delegation]: {sub_name} -> {goal}")
                            else:
                                print(f"   🛠️ [Tool Request]: {tc['name']}")
                                if 'filename' in tc['args']:
                                    print(f"      📄 [Target]: {tc['args']['filename']}")

                # 打印工具结果
                elif node == "tools" and isinstance(values, dict) and "messages" in values:
                    tool_msgs_obj = values["messages"]
                    # 兼容 Overwrite
                    tool_msgs = getattr(tool_msgs_obj, "value", tool_msgs_obj)
                    if isinstance(tool_msgs, list) and tool_msgs:
                        print(f"   ✅ [Tool Result]: {tool_msgs[-1].content}")


        print(f"\n{'='*60}")
        if final_response:
            print(f"\n📄 [最终回复]:\n{final_response}\n")
        print("\n✅ [分析流程已结束]")
        
        # 验证报告文件生成情况
        report_dir = os.path.join("src", "agents", "demo", "reports")
        if os.path.exists(report_dir):
            reports = sorted(os.listdir(report_dir), key=lambda x: os.path.getmtime(os.path.join(report_dir, x)), reverse=True)
            if reports:
                print(f"\n📊 [归档系统已就绪]:")
                print(f"   📂 存储目录: {report_dir}")
                print(f"   📑 最新产出报告:")
                # 只列出前几个最新的
                for r in reports[:3]:
                    size = os.path.getsize(os.path.join(report_dir, r))
                    print(f"     • {r} ({size} 字节)")
            else:
                print(f"\n⚠️ [异常报警]: 归档目录 {report_dir} 尚未捕获任何产出。请检查 agent_factory 提示词配置。")
        else:
             print(f"\n🚫 [系统错误]: 无法找到预设的报告存档路径: {report_dir}")

    except Exception as e:
        print(f"\n❌ [Error] 运行失败: {e}")
        import traceback
        traceback.print_exc()
        print("请检查 API 配置或网络连通性。")

if __name__ == "__main__":
    asyncio.run(run_power_analysis())
