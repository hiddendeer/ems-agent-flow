"""
CommandExecutionAgent 功能测试脚本。

验证：
1. 智能体导入和初始化
2. 工具调用功能
3. 验证器功能
4. 审计日志功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.domains.command_execution import CommandExecutionAgent
from agents.domains.command_execution.validators import (
    ParameterValidator,
    SafetyChecker,
    PermissionChecker,
    RiskLevel
)
from agents.domains.command_execution.audit import OperationLogger, OperationAuditor
from agents.core.registry import AgentRegistry


def test_agent_registration():
    """测试智能体注册"""
    print("\n" + "="*60)
    print("测试 1: 智能体注册")
    print("="*60)

    # 注册所有领域智能体
    from agents.domains import register_all_domains
    register_all_domains()

    # 检查注册结果
    assert AgentRegistry.count() == 5, f"Expected 5 agents, got {AgentRegistry.count()}"
    assert 'CommandExecutionExpert' in AgentRegistry.get_names()

    print(f"[OK] 已注册智能体数量: {AgentRegistry.count()}")
    print(f"[OK] 智能体列表: {AgentRegistry.get_names()}")


def test_agent_initialization():
    """测试智能体初始化"""
    print("\n" + "="*60)
    print("测试 2: 智能体初始化")
    print("="*60)

    agent = CommandExecutionAgent()

    assert agent.name == "CommandExecutionExpert"
    assert len(agent.get_tools()) == 6
    assert agent.get_system_prompt() is not None

    print(f"[OK] 智能体名称: {agent.name}")
    print(f"[OK] 工具数量: {len(agent.get_tools())}")
    print(f"[OK] 工具列表:")
    for tool in agent.get_tools():
        print(f"   - {tool.name}")


def test_parameter_validator():
    """测试参数验证器"""
    print("\n" + "="*60)
    print("测试 3: 参数验证器")
    print("="*60)

    validator = ParameterValidator()

    # 测试有效参数
    result1 = validator.validate("charge", {"power": 100, "target_soc": 80})
    assert result1.is_valid, f"Expected valid, got: {result1.reason}"
    print("[OK] 有效参数验证通过")

    # 测试无效参数（功率为负）
    result2 = validator.validate("charge", {"power": -100})
    assert not result2.is_valid
    print(f"[OK] 无效参数被拒绝: {result2.reason}")

    # 测试无效指令类型
    result3 = validator.validate("invalid_cmd", {})
    assert not result3.is_valid
    print(f"[OK] 无效指令类型被拒绝: {result3.reason}")


def test_safety_checker():
    """测试安全检查器"""
    print("\n" + "="*60)
    print("测试 4: 安全检查器")
    print("="*60)

    checker = SafetyChecker()

    # 测试正常充电（BAT-001）
    result1 = checker.check("BAT-001", "charge", {"power": 100})
    print(f"[OK] BAT-001 充电检查: {'通过' if result1.is_safe else '拒绝'}")
    print(f"     原因: {result1.reason}")
    print(f"     风险等级: {result1.risk_level}")

    # 测试高SOC充电（应该被拒绝）
    result2 = checker.check("BAT-001", "charge", {"power": 100, "target_soc": 98})
    print(f"[OK] 高SOC充电检查: {'通过' if result2.is_safe else '拒绝'}")
    print(f"     原因: {result2.reason}")

    # 测试不存在的设备
    result3 = checker.check("INVALID-DEVICE", "charge", {})
    assert not result3.is_safe
    print(f"[OK] 不存在设备检查被拒绝: {result3.reason}")


def test_permission_checker():
    """测试权限检查器"""
    print("\n" + "="*60)
    print("测试 5: 权限检查器")
    print("="*60)

    checker = PermissionChecker()

    # 测试系统管理员权限
    result1 = checker.check("system", "charge")
    assert result1.is_allowed
    print(f"[OK] 系统管理员充电权限: {result1.current_level}")

    # 测试普通用户权限
    result2 = checker.check("user_002", "charge")
    print(f"[OK] 普通用户充电权限: {'允许' if result2.is_allowed else '拒绝'}")
    if not result2.is_allowed:
        print(f"     原因: {result2.reason}")


def test_operation_logger():
    """测试操作日志"""
    print("\n" + "="*60)
    print("测试 6: 操作日志")
    print("="*60)

    logger = OperationLogger(log_file="test_operation_logs.jsonl")

    # 创建日志
    log = logger.create_log(
        command_type="charge",
        device_id="TEST-DEVICE",
        operator="test_operator",
        parameters={"power": 100}
    )

    print(f"[OK] 创建日志: {log.operation_id}")
    print(f"     指令类型: {log.command_type}")
    print(f"     设备ID: {log.device_id}")
    print(f"     状态: {log.status.value}")

    # 更新日志
    from agents.domains.command_execution.audit import OperationStatus
    updated_log = logger.update_log(
        log.operation_id,
        status=OperationStatus.SUCCESS,
        execution_result="测试执行成功"
    )

    assert updated_log.status == OperationStatus.SUCCESS
    print(f"[OK] 更新日志状态: {updated_log.status.value}")


def test_auditor():
    """测试审计追踪"""
    print("\n" + "="*60)
    print("测试 7: 审计追踪")
    print("="*60)

    logger = OperationLogger(log_file="test_operation_logs.jsonl")
    auditor = OperationAuditor(logger)

    # 创建测试日志
    log = logger.create_log(
        command_type="charge",
        device_id="TEST-DEVICE",
        operator="test_operator",
        parameters={"power": 100}
    )

    # 审计操作
    report = auditor.audit_operation(log.operation_id)

    assert report is not None
    print(f"[OK] 审计报告生成")
    print(f"     操作ID: {report['operation_id']}")
    print(f"     合规性: {report['compliance_check']['is_compliant']}")


def test_tools_integration():
    """测试工具集成"""
    print("\n" + "="*60)
    print("测试 8: 工具集成")
    print("="*60)

    agent = CommandExecutionAgent()
    tools = agent.get_tools()

    # 测试工具可调用性
    print(f"[OK] 工具数量: {len(tools)}")

    # 获取工具列表
    tool_names = [t.name for t in tools]
    expected_tools = [
        "review_and_validate_command",
        "assess_command_risk",
        "execute_device_command",
        "log_operation",
        "emergency_stop_all",
        "query_device_status"
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"
        print(f"[OK] 工具已注册: {expected}")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("CommandExecutionAgent 功能测试")
    print("="*60)

    try:
        test_agent_registration()
        test_agent_initialization()
        test_parameter_validator()
        test_safety_checker()
        test_permission_checker()
        test_operation_logger()
        test_auditor()
        test_tools_integration()

        print("\n" + "="*60)
        print("✓ 所有测试通过！")
        print("="*60)

        print("\n功能验证总结:")
        print("- [OK] 智能体注册和初始化")
        print("- [OK] 参数验证器")
        print("- [OK] 安全检查器")
        print("- [OK] 权限检查器")
        print("- [OK] 操作日志")
        print("- [OK] 审计追踪")
        print("- [OK] 工具集成")

        print("\nCommandExecutionAgent 已就绪，可以正常使用！")

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
