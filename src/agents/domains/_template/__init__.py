"""
新领域 Agent 开发模板。

如何新增一个领域 Agent：
    1. 复制本目录（_template）到 domains/ 下，重命名为你的领域名称
    2. 在 tools/__init__.py 中定义领域专用工具
    3. 在 skills/ 目录下创建子目录，并编写 SKILL.md (内含 description 前置元数据)
    4. 在 prompts.py 中编写系统提示词
    5. 在 agent.py 中实现 get_tools() 和 get_system_prompt()
    6. [可选] 在 agent.py 中重写 get_skills() 以暴露技能目录
    7. 在 domains/__init__.py 中导入该模块以触发自动注册
"""
