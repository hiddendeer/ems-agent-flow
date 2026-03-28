"""
诊断并修复 skills 字段验证错误。

问题分析：
1. Pydantic 错误显示 skills 字段期望 list，但收到 str
2. 可能是服务器进程缓存了旧代码
3. 或者某个 agent 的 get_skills() 返回了错误的类型

解决方案：
1. 检查所有 agent 的 get_skills() 返回值
2. 修复任何返回字符串的问题
3. 提供服务器重启建议
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def check_all_agents():
    """检查所有 agent 的 get_skills 返回值"""
    print("="*80)
    print("诊断所有 Agent 的 get_skills() 方法")
    print("="*80)

    from agents.domains import register_all_domains
    from agents.core.registry import AgentRegistry

    # 清除可能的模块缓存
    modules_to_clear = [key for key in sys.modules.keys() if key.startswith('agents')]
    for module in modules_to_clear:
        del sys.modules[module]

    register_all_domains()

    issues = []

    for name, agent in AgentRegistry._agents.items():
        skills = agent.get_skills()
        print(f"\n智能体: {name}")
        print(f"  返回类型: {type(skills)}")

        if skills is None:
            print(f"  返回值: None")
            print(f"  状态: OK (未使用 skills)")
        elif isinstance(skills, list):
            print(f"  列表长度: {len(skills)}")
            for i, skill in enumerate(skills):
                print(f"    [{i}] {skill}")
                # 检查是文件还是目录
                if os.path.exists(skill):
                    if os.path.isfile(skill):
                        print(f"        类型: 文件 ✓")
                    elif os.path.isdir(skill):
                        print(f"        类型: 目录 ⚠ (可能需要改为文件路径列表)")
                else:
                    print(f"        状态: 路径不存在 ✗")
            print(f"  状态: OK")
        else:
            print(f"  返回值: {skills}")
            print(f"  状态: ✗ 错误 - 应该返回 list 或 None")
            issues.append((name, type(skills), skills))

    print("\n" + "="*80)
    print("诊断结果")
    print("="*80)

    if issues:
        print(f"\n发现 {len(issues)} 个问题：")
        for name, return_type, value in issues:
            print(f"\n✗ {name}:")
            print(f"  返回类型: {return_type}")
            print(f"  返回值: {value}")
            print(f"  期望: Optional[List[str]]")
        return False
    else:
        print("\n✅ 所有 Agent 的 get_skills() 方法都正确！")
        return True


def test_subagent_generation():
    """测试 subagent 配置生成"""
    print("\n" + "="*80)
    print("测试 SubAgent 配置生成")
    print("="*80)

    from agents.domains import register_all_domains
    from agents.core.registry import AgentRegistry

    register_all_domains()

    try:
        configs = AgentRegistry.get_subagent_configs()
        print(f"\n✅ 成功生成 {len(configs)} 个 SubAgent 配置")
        return True
    except Exception as e:
        print(f"\n✗ 生成配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_solution():
    """打印解决方案"""
    print("\n" + "="*80)
    print("解决方案")
    print("="*80)

    print("""
如果诊断显示代码正确但服务器仍然报错，请执行以下步骤：

1. **重启服务器进程**
   ```bash
   # 停止当前服务器进程
   # 然后重新启动
   ```

2. **清除 Python 缓存**
   ```bash
   # Windows
   find . -type d -name __pycache__ -exec rm -rf {} +
   find . -name "*.pyc" -delete

   # 或者在 PowerShell 中
   Get-ChildItem -Path . -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
   Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
   ```

3. **确认代码更新**
   - 检查 src/agents/domains/command_execution/agent.py
   - 确认 get_skills() 方法返回 Optional[List[str]]

4. **检查环境变量**
   - 确保没有使用缓存的环境变量
   - 确保 PYTHONPATH 指向正确的目录

5. **如果问题仍然存在**
   - 检查是否有多个 agent 实例被注册
   - 检查 AgentRegistry 是否有重复的 agent
   - 完全重启应用服务器
    """)


def main():
    """主函数"""
    print("\n" + "="*80)
    print("Skills 字段验证错误诊断工具")
    print("="*80)

    # 检查所有 agent
    agents_ok = check_all_agents()

    # 测试配置生成
    configs_ok = test_subagent_generation()

    # 打印解决方案
    print_solution()

    # 总结
    print("\n" + "="*80)
    print("总结")
    print("="*80)

    if agents_ok and configs_ok:
        print("\n✅ 代码层面没有问题！")
        print("\n如果服务器仍然报错，请重启服务器进程。")
        print("Python 可能缓存了旧版本的模块。")
    else:
        print("\n✗ 发现代码问题，请修复后重试。")


if __name__ == "__main__":
    main()
