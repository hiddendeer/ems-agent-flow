# 测试文件目录

本目录包含所有测试脚本。

## 📁 文件列表

### CommandExecutionAgent 测试

#### [test_command_execution.py](test_command_execution.py)
CommandExecutionAgent 功能验证测试。

**测试内容**：
- 智能体注册
- 智能体初始化
- 参数验证器
- 安全检查器
- 权限检查器
- 操作日志
- 审计追踪
- 工具集成

**运行方式**：
```bash
python tests/test_command_execution.py
```

---

#### [test_command_execution_interactive.py](test_command_execution_interactive.py)
CommandExecutionAgent 交互式测试脚本。

**测试方式**：
1. 直接调用工具（适合开发者）
2. 通过 Lead Agent 调度（推荐）
3. 交互式对话模式（用户体验）
4. 预设场景测试（快速验证）

**运行方式**：
```bash
python tests/test_command_execution_interactive.py
```

---

### 其他测试

- `test_health.py` - 健康检查测试
- `conftest.py` - pytest 配置
- `demo/` - 演示脚本目录

---

## 🚀 快速开始

### 运行功能验证测试

```bash
python tests/test_command_execution.py
```

### 运行交互式测试

```bash
python tests/test_command_execution_interactive.py
```

然后选择测试方式（推荐选择 **选项3** 进入交互式对话模式）。

---

## 📝 注意事项

1. 所有测试脚本都需要在项目根目录下运行
2. 测试前请确保已安装所有依赖
3. 交互式测试需要人工输入，请按照提示操作
4. 测试过程中会创建临时日志文件，测试结束后可删除

---

## 🔗 相关文档

- [实现完成报告](../Mark/COMMAND_EXECUTION_AGENT_REPORT.md)
- [使用指南](../Mark/COMMAND_EXECUTION_USAGE.md)
