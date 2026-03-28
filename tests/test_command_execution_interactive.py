"""
CommandExecutionAgent 交互式测试脚本。

演示如何与 CommandExecutionAgent 对话并执行指令。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.domains.command_execution import CommandExecutionAgent
from agents.core.factory import create_ems_agent


def test_direct_tool_usage():
    """方式1: 直接调用工具"""
    print("\n" + "="*80)
    print("方式1: 直接调用工具")
    print("="*80)

    # 创建智能体实例
    agent = CommandExecutionAgent()
    tools = {t.name: t for t in agent.get_tools()}

    print("\n[步骤1] 查询设备状态...")
    status = tools["query_device_status"].invoke({"device_id": "BAT-001"})
    print(status)

    print("\n[步骤2] 审查充电指令...")
    review = tools["review_and_validate_command"].invoke({
        "command_type": "charge",
        "device_id": "BAT-001",
        "parameters": {"power": 100, "target_soc": 80},
        "operator": "system"
    })
    print(review)

    print("\n[步骤3] 评估风险...")
    risk = tools["assess_command_risk"].invoke({
        "command_type": "charge",
        "device_id": "BAT-001",
        "parameters": {"power": 100, "target_soc": 80}
    })
    print(risk)

    print("\n[步骤4] 执行指令...")
    exec_result = tools["execute_device_command"].invoke({
        "command_type": "charge",
        "device_id": "BAT-001",
        "parameters": {"power": 100, "target_soc": 80},
        "operator": "system"
    })
    print(exec_result)


def test_with_lead_agent():
    """方式2: 通过 Lead Agent 调度"""
    print("\n" + "="*80)
    print("方式2: 通过 Lead Agent 调度（推荐）")
    print("="*80)

    # 创建 Lead Agent
    print("\n[初始化] 创建 Lead Agent...")
    lead_agent = create_ems_agent()

    print("\n[任务] 让 Lead Agent 执行充电指令...")
    result = lead_agent.invoke(
        "请帮我执行一个充电指令："
        "\n- 设备ID: BAT-001"
        "\n- 充电功率: 100kW"
        "\n- 目标SOC: 80%"
    )

    print("\n[结果]")
    print(result)


def interactive_mode():
    """方式3: 交互式对话"""
    print("\n" + "="*80)
    print("方式3: 交互式对话模式")
    print("="*80)

    # 创建 Lead Agent
    lead_agent = create_ems_agent()

    print("\n已进入交互式对话模式。")
    print("你可以输入以下类型的指令：")
    print("  1. 执行充电指令：帮我给BAT-001充电，功率100kW，目标SOC 80%")
    print("  2. 执行放电指令：BAT-002放电，功率200kW，持续2小时")
    print("  3. 查询设备状态：查询BAT-001的当前状态")
    print("  4. 停止设备：停止BAT-001的运行")
    print("  5. 紧急停止：紧急停止所有设备")
    print("\n输入 'quit' 或 'exit' 退出\n")

    while True:
        try:
            user_input = input("\n>>> 请输入指令: ").strip()

            if user_input.lower() in ['quit', 'exit', '退出']:
                print("再见！")
                break

            if not user_input:
                continue

            print(f"\n[执行中...]")
            result = lead_agent.invoke(user_input)
            print(f"\n[回复]\n{result}")

        except KeyboardInterrupt:
            print("\n\n检测到中断，退出...")
            break
        except Exception as e:
            print(f"\n[错误] {str(e)}")


def test_scenarios():
    """方式4: 预设场景测试"""
    print("\n" + "="*80)
    print("方式4: 预设场景测试")
    print("="*80)

    agent = CommandExecutionAgent()
    tools = {t.name: t for t in agent.get_tools()}

    scenarios = [
        {
            "name": "场景1: 正常充电",
            "device": "BAT-001",
            "command": "charge",
            "params": {"power": 100, "target_soc": 80}
        },
        {
            "name": "场景2: 查询状态",
            "device": "BAT-002",
            "command": "query",
            "params": {}
        },
        {
            "name": "场景3: 放电指令",
            "device": "BAT-001",
            "command": "discharge",
            "params": {"power": 150, "min_soc": 20, "duration": 120}
        },
        {
            "name": "场景4: 停止设备",
            "device": "BAT-001",
            "command": "stop",
            "params": {}
        }
    ]

    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"{scenario['name']}")
        print(f"{'='*60}")

        if scenario['command'] == "query":
            result = tools["query_device_status"].invoke({
                "device_id": scenario['device']
            })
        elif scenario['command'] == "stop":
            result = tools["execute_device_command"].invoke({
                "command_type": "stop",
                "device_id": scenario['device'],
                "parameters": scenario['params'],
                "operator": "system"
            })
        else:
            # 先审查
            review = tools["review_and_validate_command"].invoke({
                "command_type": scenario['command'],
                "device_id": scenario['device'],
                "parameters": scenario['params'],
                "operator": "system"
            })
            print(f"[审查结果]\n{review}\n")

            # 如果审查通过，执行
            if "✅" in review:
                exec_result = tools["execute_device_command"].invoke({
                    "command_type": scenario['command'],
                    "device_id": scenario['device'],
                    "parameters": scenario['params'],
                    "operator": "system"
                })
                result = exec_result
            else:
                result = "指令未通过审查，拒绝执行"

        print(f"[执行结果]\n{result}")


def main():
    """主菜单"""
    print("\n" + "="*80)
    print("CommandExecutionAgent 测试脚本")
    print("="*80)

    print("\n请选择测试方式：")
    print("  1. 直接调用工具（适合开发者）")
    print("  2. 通过 Lead Agent 调度（推荐）")
    print("  3. 交互式对话模式（用户体验）")
    print("  4. 预设场景测试（快速验证）")
    print("  5. 运行所有测试")

    choice = input("\n请输入选项 (1-5): ").strip()

    if choice == "1":
        test_direct_tool_usage()
    elif choice == "2":
        test_with_lead_agent()
    elif choice == "3":
        interactive_mode()
    elif choice == "4":
        test_scenarios()
    elif choice == "5":
        test_direct_tool_usage()
        test_with_lead_agent()
        test_scenarios()
    else:
        print("无效选项，运行默认测试...")
        test_direct_tool_usage()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
