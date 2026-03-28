"""
验证 CommandExecutionAgent 修复后的功能。

修复内容：
- get_skills() 方法现在返回 List[str] 而不是 str
- 返回技能文件路径列表，而不是目录路径
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.domains.command_execution import CommandExecutionAgent
from agents.core.factory import create_ems_agent


def test_get_skills():
    """测试 get_skills 返回类型"""
    print("\n" + "="*80)
    print("测试 1: get_skills 返回类型")
    print("="*80)

    agent = CommandExecutionAgent()
    skills = agent.get_skills()

    print(f"✓ 返回类型: {type(skills)}")
    print(f"✓ 返回值: {skills}")

    assert isinstance(skills, list), f"Expected list, got {type(skills)}"
    assert len(skills) > 0, "Skills list should not be empty"

    for skill in skills:
        assert isinstance(skill, str), f"Skill path should be str, got {type(skill)}"
        assert skill.endswith('.md'), f"Skill file should end with .md: {skill}"
        print(f"  ✓ 技能文件: {skill}")

    print("\n✅ get_skills 测试通过")


def test_agent_registration():
    """测试智能体注册"""
    print("\n" + "="*80)
    print("测试 2: 智能体注册")
    print("="*80)

    from agents.domains import register_all_domains
    from agents.core.registry import AgentRegistry

    register_all_domains()

    count = AgentRegistry.count()
    names = AgentRegistry.get_names()

    print(f"✓ 已注册智能体数量: {count}")
    print(f"✓ 智能体列表: {names}")

    assert 'CommandExecutionExpert' in names

    print("\n✅ 智能体注册测试通过")


def test_subagent_configs():
    """测试生成 subagent 配置"""
    print("\n" + "="*80)
    print("测试 3: 生成 SubAgent 配置")
    print("="*80)

    from agents.domains import register_all_domains
    from agents.core.registry import AgentRegistry

    register_all_domains()

    configs = AgentRegistry.get_subagent_configs()

    print(f"✓ 配置数量: {len(configs)}")

    for config in configs:
        print(f"\n  智能体: {config['name']}")
        print(f"  - 工具数量: {len(config['tools'])}")
        print(f"  - 技能数量: {len(config['skills']) if config['skills'] else 0}")
        if config['skills']:
            for skill in config['skills']:
                print(f"    • {skill}")

    print("\n✅ SubAgent 配置生成测试通过")


def test_lead_agent_creation():
    """测试 Lead Agent 创建"""
    print("\n" + "="*80)
    print("测试 4: Lead Agent 创建")
    print("="*80)

    print("正在创建 Lead Agent...")
    agent = create_ems_agent()

    print(f"✓ Agent 类型: {type(agent).__name__}")
    print(f"✓ Agent 已成功创建")

    print("\n✅ Lead Agent 创建测试通过")


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("CommandExecutionAgent 修复验证测试")
    print("="*80)

    try:
        test_get_skills()
        test_agent_registration()
        test_subagent_configs()
        test_lead_agent_creation()

        print("\n" + "="*80)
        print("✅ 所有测试通过！")
        print("="*80)
        print("\n修复总结:")
        print("- [OK] get_skills() 返回 List[str]")
        print("- [OK] 智能体注册成功")
        print("- [OK] SubAgent 配置生成成功")
        print("- [OK] Lead Agent 创建成功")
        print("\nCommandExecutionAgent 已就绪！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
