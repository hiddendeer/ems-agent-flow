# 服务器重启指南 - 解决 Pydantic 验证错误

## 问题分析

**错误信息**:
```
1 validation error for DomainAgentSchema
skills
  Input should be a valid list [type=list_type, input_value='E:\\...\\skills', input_type=str]
```

**根本原因**: 服务器进程缓存了旧版本的代码

**代码状态**: ✅ 已修复（`get_skills()` 现在正确返回 `Optional[List[str]]`）

---

## 解决方案

### 1️⃣ 重启服务器（最重要）

```bash
# 停止服务器
# Ctrl+C 或 kill 进程

# 重新启动服务器
# 重新运行启动命令
```

**为什么需要重启**:
- Python 在启动时加载模块
- 运行时不会自动重新加载已修改的模块
- 必须重启进程才能加载新代码

---

### 2️⃣ 清除 Python 缓存（可选但推荐）

```powershell
# Windows PowerShell
Get-ChildItem -Path src -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Path src -Recurse -Filter "*.pyc" | Remove-Item -Force
```

```bash
# Git Bash / Linux
find src -type d -name __pycache__ -exec rm -rf {} +
find src -name "*.pyc" -delete
```

---

### 3️⃣ 验证代码更新

```bash
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
```

**期望输出**:
```
Type: <class 'list'>
Value: ['E:\\EMS\\ems-agent-flow\\src\\agents\\domains\\command_execution\\skills\\SKILL.md']
```

---

### 4️⃣ 检查是否有多个 Python 进程

```powershell
# 查看所有 Python 进程
tasklist | findstr python

# 如果有多个，可能需要全部停止
```

---

### 5️⃣ 测试 API

重启服务器后，再次测试 API：

```
POST /api/v1/projectApi/chat/stream
```

应该不再出现 Pydantic 验证错误。

---

## 常见问题

### Q: 为什么代码改了，服务器还在报错？

**A**: Python 模块缓存。服务器进程在启动时加载模块，运行时不会自动更新。

### Q: 清除缓存安全吗？

**A**: 安全。`__pycache__` 和 `.pyc` 文件是 Python 自动生成的字节码缓存，删除后会自动重新生成。

### Q: 重启后还有问题怎么办？

**A**: 可能的原因：
- IDE 调试器缓存：重启 IDE
- 虚拟环境问题：确认使用正确的虚拟环境
- Docker/容器：重建镜像
- 多个 Python 进程：确认所有进程都已重启

---

## 快速检查清单

- [ ] 停止服务器进程
- [ ] 清除 Python 缓存
- [ ] 重新启动服务器
- [ ] 测试 API 调用
- [ ] 确认错误已解决

---

## 技术细节

### 修复的代码

**文件**: `src/agents/domains/command_execution/agent.py`

**修改前**:
```python
def get_skills(self) -> str:
    """返回执行规范和安全协议技能目录"""
    from pathlib import Path
    skills_path = Path(__file__).parent / "skills"
    return str(skills_path)  # ❌ 返回字符串
```

**修改后**:
```python
def get_skills(self) -> Optional[List[str]]:
    """返回执行规范和安全协议技能文件列表"""
    from pathlib import Path
    skills_path = Path(__file__).parent / "skills"
    if skills_path.exists():
        return [str(f) for f in skills_path.glob("*.md")]  # ✅ 返回列表
    return None
```

### 验证状态

```bash
# 所有 agent 的 get_skills() 方法都正确
EnergyStorageExpert: None ✓
PowerMarketExpert: list ✓
PowerSearchExpert: None ✓
PyPSAModelingExpert: None ✓
CommandExecutionExpert: list ✓
```

---

## 总结

✅ **代码层面**: 已修复
⚠️ **服务器状态**: 需要重启
🔄 **下一步**: 重启服务器 → 清除缓存 → 测试 API

---

**创建日期**: 2026-03-28
**问题状态**: 代码已修复，等待服务器重启验证
