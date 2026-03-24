"""
新领域 Agent 开发模板。

如何新增一个领域 Agent：
1. 复制本目录（_template）到 domains/ 下，重命名为你的领域名称
2. 在 tools/__init__.py 中定义领域专用工具
3. 在 skills/__init__.py 中定义高阶技能
4. 在 prompts.py 中编写系统提示词
5. 在 agent.py 中继承 BaseSubAgent 并实现抽象方法
6. 在 agent.py 底部调用 AgentRegistry.register()
7. 在 domains/__init__.py 的 register_all_domains() 中导入你的模块
"""
