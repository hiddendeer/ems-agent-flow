# CommandExecutionAgent 使用指南

## 🚀 快速开始

### 方式1: 运行交互式测试脚本（推荐）

```bash
# 在项目根目录运行
python test_command_execution_interactive.py
```

然后选择测试方式：
- **选项1**: 直接调用工具（适合开发者调试）
- **选项2**: 通过 Lead Agent 调度（推荐，模拟真实场景）
- **选项3**: 交互式对话模式（用户体验最佳）
- **选项4**: 预设场景测试（快速验证功能）
- **选项5**: 运行所有测试

---

### 方式2: 直接运行 Python 脚本

```python
# test_simple.py
import sys
sys.path.insert(0, 'src')

from agents.domains.command_execution import CommandExecutionAgent

# 创建智能体
agent = CommandExecutionAgent()
tools = {t.name: t for t in agent.get_tools()}

# 1. 查询设备状态
print("=== 查询设备状态 ===")
status = tools["query_device_status"].invoke({"device_id": "BAT-001"})
print(status)

# 2. 审查指令
print("\n=== 审查充电指令 ===")
review = tools["review_and_validate_command"].invoke({
    "command_type": "charge",
    "device_id": "BAT-001",
    "parameters": {"power": 100, "target_soc": 80},
    "operator": "system"
})
print(review)

# 3. 执行指令
print("\n=== 执行充电指令 ===")
exec_result = tools["execute_device_command"].invoke({
    "command_type": "charge",
    "device_id": "BAT-001",
    "parameters": {"power": 100, "target_soc": 80},
    "operator": "system"
})
print(exec_result)
```

运行：
```bash
python test_simple.py
```

---

### 方式3: 使用 Lead Agent 对话（最简单）

```python
# test_lead_agent.py
import sys
sys.path.insert(0, 'src')

from agents.core.factory import create_ems_agent

# 创建 Lead Agent
lead_agent = create_ems_agent()

# 直接对话
result = lead_agent.invoke("""
请帮我执行一个充电指令：
- 设备ID: BAT-001
- 充电功率: 100kW
- 目标SOC: 80%
""")

print(result)
```

---

## 💬 对话示例

### 示例1: 正常充电指令

**用户输入：**
```
请帮我给BAT-001充电，功率100kW，目标SOC 80%
```

**Agent回复：**
```
✅ 指令审查通过
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 指令详情:
   • 指令类型: charge
   • 目标设备: BAT-001
   • 操作者: system
   • 参数: {'power': 100, 'target_soc': 80}
⚠️  风险等级: 低
🔍 审查结果:
   • ✅ 参数验证通过
   • ✅ 安全检查通过
   • ✅ 权限验证通过
▶️  可以执行，请继续调用执行工具

✅ 指令执行成功
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 操作详情:
   • 操作ID: OP-20260328103000-BAT-001
   • 设备ID: BAT-001
   • 指令类型: charge
⚡ 执行参数:
   • {'power': 100, 'target_soc': 80}
📊 当前状态:
   • 设备状态: charging
   • 当前功率: 100kW
✨ 指令已成功下发并执行
```

---

### 示例2: 查询设备状态

**用户输入：**
```
查询BAT-001的当前状态
```

**Agent回复：**
```
📊 设备状态查询
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 设备ID: BAT-001
🔧 运行状态: charging
⚡ 当前功率: 100 kW
🔺 电压: 380 V
🔻 电流: 263 A
🔋 SOC: 45.0%
💊 SOH: 98.5%
🌡️  温度: 25.0℃
📅 最后更新: 2026-03-28T10:00:00Z
```

---

### 示例3: 放电指令

**用户输入：**
```
BAT-002需要放电，功率200kW，最低SOC不要低于20%
```

**Agent回复：**
```
✅ 指令审查通过
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 指令详情:
   • 指令类型: discharge
   • 目标设备: BAT-002
   • 参数: {'power': 200, 'min_soc': 20}
⚠️  风险等级: 中
▶️  可以执行

✅ 指令执行成功
📋 操作ID: OP-20260328103100-BAT-002
⚡ 设备BAT-002已启动放电程序
📊 当前SOC: 78% → 最低: 20%
```

---

### 示例4: 停止设备

**用户输入：**
```
停止BAT-001的充电
```

**Agent回复：**
```
✅ 指令执行成功
📋 操作ID: OP-20260328103200-BAT-001
⚡ 设备BAT-001已停止运行
📊 当前状态: charging → standby
```

---

### 示例5: 紧急停止

**用户输入：**
```
紧急停止所有设备！
```

**Agent回复：**
```
🚨 紧急停止已执行
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⛔ 停止范围: 所有设备
🚫 停止原因: 未指定
📊 受影响设备: 2 台
📋 设备列表: BAT-001, BAT-002
⚠️  警告: 所有设备已停止，需要人工确认才能恢复运行
```

---

## 📋 可用指令类型

### 充电指令
```
给BAT-001充电，功率100kW，目标SOC 80%
BAT-001充电到90%，功率200kW
启动BAT-002充电程序，功率150kW，持续2小时
```

### 放电指令
```
BAT-001放电，功率200kW
BAT-002放电500kWh，最低SOC 20%
执行放电指令：BAT-001，功率300kW，持续4小时
```

### 停止指令
```
停止BAT-001
停止所有设备的运行
BAT-001停止充电
```

### 查询指令
```
查询BAT-001的状态
查看所有设备的运行状态
BAT-002的当前SOC是多少？
```

### 紧急指令
```
紧急停止所有设备
紧急停止BAT-001
系统紧急停机
```

---

## 🛡️ 安全机制

### 自动审查
所有指令都会自动进行：
- ✅ 参数验证（类型、范围、完整性）
- ✅ 安全检查（设备状态、时序冲突、安全阈值）
- ✅ 权限验证（操作者权限级别）

### 风险评估
- 🟢 **低风险**: 自动执行
- 🟡 **中风险**: 提示确认
- 🟠 **高风险**: 建议二次确认
- 🔴 **严重风险**: 必须明确确认

### 审计日志
所有操作都会记录：
- 操作ID
- 操作类型
- 设备ID
- 操作者
- 执行状态
- 时间戳

---

## 🔧 高级用法

### 自定义设备状态

```python
from agents.domains.command_execution.validators.safety_checker import SafetyChecker

# 更新设备状态
SafetyChecker().update_device_state("BAT-003", {
    "status": "standby",
    "soc": 60.0,
    "soh": 95.0,
    "temperature": 28.0,
    "voltage": 385.0,
    "current": 0.0,
    "power": 0.0,
    "capacity": 800
})
```

### 查看操作日志

```python
from agents.domains.command_execution.audit import get_logger

logger = get_logger()

# 获取最近日志
recent_logs = logger.get_recent_logs(limit=10)
for log in recent_logs:
    print(f"{log.operation_id}: {log.status.value}")

# 获取统计信息
stats = logger.get_statistics()
print(stats)
```

---

## ❓ 常见问题

### Q: 为什么指令被拒绝？
A: 可能的原因：
- 参数超出安全范围
- 设备状态不兼容（如电池已满时继续充电）
- 操作权限不足
- 设备故障或离线

### Q: 如何查看设备状态？
A: 使用查询指令：
```
查询BAT-001的状态
```

### Q: 如何停止正在执行的指令？
A: 使用停止指令：
```
停止BAT-001
```

### Q: 紧急情况如何处理？
A: 使用紧急停止：
```
紧急停止所有设备
```

---

## 📞 技术支持

如有问题，请查看：
- [实现完成报告](COMMAND_EXECUTION_AGENT_REPORT.md)
- [功能测试脚本](test_command_execution.py)
- [交互式测试脚本](test_command_execution_interactive.py)

---

**祝使用愉快！** 🎉
