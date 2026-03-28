"""
服务器重启和缓存清除指南。

问题：Pydantic 验证错误 - skills 字段期望 list 但收到 str
原因：服务器进程缓存了旧版本的代码
解决方案：重启服务器并清除 Python 缓存
"""

print("""
================================================================================
问题解决方案
================================================================================

问题分析：
-----------
代码层面已经修复（get_skills() 正确返回 list），但服务器仍在报错。
这是 Python 模块缓存导致的。

解决方案：
-----------""")

print("""
1. 【最重要】重启服务器进程
   """)
print("""
   - 停止当前运行的服务器（Ctrl+C 或 kill 进程）
   - 重新启动服务器
   - Python 会在启动时重新加载所有模块
   """)

print("""
2. 清除 Python 字节码缓存
   """)
print("""
   # Windows PowerShell
   Get-ChildItem -Path src -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
   Get-ChildItem -Path src -Recurse -Filter "*.pyc" | Remove-Item -Force

   # 或使用 find（如果安装了 Git Bash）
   find src -type d -name __pycache__ -exec rm -rf {} +
   find src -name "*.pyc" -delete
   """)

print("""
3. 确认代码更新
   """)
print("""
   # 检查 CommandExecutionAgent 的 get_skills 方法
   cd e:/EMS/ems-agent-flow
   python -c "
   import sys
   sys.path.insert(0, 'src')
   from agents.domains.command_execution import CommandExecutionAgent
   agent = CommandExecutionAgent()
   skills = agent.get_skills()
   print(f'Type: {type(skills)}')
   print(f'Value: {skills}')
   "

   # 应该输出：
   # Type: <class 'list'>
   # Value: ['E:\\...\\skills\\SKILL.md']
   """)

print("""
4. 检查是否有多个 Python 进程
   """)
print("""
   # Windows Task Manager 或命令行
   tasklist | findstr python

   # 如果看到多个 python.exe 进程，可能需要全部停止后重启
   """)

print("""
5. 验证修复
   """)
print("""
   重启服务器后，再次测试 API：
   POST /api/v1/projectApi/chat/stream

   应该不再出现 Pydantic 验证错误
   """)

print("""
6. 如果问题仍然存在
   """)
print("""
   可能的原因：
   - IDE 调试器缓存：如果是用 IDE 运行，尝试重启 IDE
   - 环境变量问题：检查 PYTHONPATH 是否指向错误的目录
   - 虚拟环境问题：确认使用的是正确的虚拟环境
   - Docker/容器：如果使用容器，需要重建镜像

   最后的手段：
   - 完全重启计算机（清除所有可能的缓存）
   - 重新创建虚拟环境
   """)

print("""
================================================================================
快速检查脚本
================================================================================
""")

print("""
# 运行此脚本验证代码是否正确
python -c "
import sys
sys.path.insert(0, 'src')
from agents.domains import register_all_domains
from agents.core.registry import AgentRegistry
register_all_domains()
configs = AgentRegistry.get_subagent_configs()
print('SUCCESS: All agents configured correctly')
print(f'Number of agents: {len(configs)}')
"
""")

print("""
================================================================================
总结
================================================================================

代码已经正确修复，问题是服务器进程缓存。

【关键步骤】：
1. 停止服务器
2. 清除 Python 缓存（可选但推荐）
3. 重新启动服务器
4. 测试 API

如果问题仍然存在，请提供：
- 完整的错误堆栈
- 服务器启动命令
- Python 版本和依赖列表
""")
