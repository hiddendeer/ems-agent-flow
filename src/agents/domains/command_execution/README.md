# 执行层智能体 - 结构化提案设计

## 架构设计

### 职责分离

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent 层 (决策层)                         │
│                                                              │
│  1. 指令安全审查                                               │
│  2. 风险评估                                                  │
│  3. 生成【执行提案】                                           │
│  4. 记录审计日志                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ 返回结构化提案 (JSON)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    业务 API 层 (执行层)                        │
│                                                              │
│  1. 验证提案签名                                              │
│  2. 检查设备状态                                              │
│  3. 调用设备 API                                             │
│  4. 处理执行结果                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP 请求
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    设备层 (BMS/PCS)                           │
└─────────────────────────────────────────────────────────────┘
```

## 核心优势

### ✅ 安全性
- Agent 不直接访问设备和数据库
- 执行逻辑在业务层控制
- 提案签名验证，防止伪造

### ✅ 可测试性
- Agent 层：测试决策逻辑，不需要 mock 设备
- API 层：测试执行逻辑，不需要跑 LLM

### ✅ 可复用性
- 同一个 API 可被多个入口调用（UI、调度系统、Agent）
- 统一的执行入口和日志记录

### ✅ 可追溯性
- 提案生成（决策层）→ 提案执行（执行层）
- 职责清晰，便于问题定位

## 数据结构

### ExecutionProposal（执行提案）

```json
{
  "proposal_id": "PROP-20260403-a1b2c3d4",
  "status": "pending_execution",
  "created_at": "2026-04-03T10:30:00Z",
  
  "target": {
    "device_id": "dev_001",
    "device_type": "PCS",
    "command_type": "charge",
    "api_endpoint": "/api/v1/devices/pcs/charge",
    "http_method": "POST",
    "parameters": [
      {
        "name": "power",
        "value": 100.0,
        "data_type": "float",
        "unit": "kW",
        "range": {"min": 0, "max": 500},
        "required": true
      },
      {
        "name": "target_soc",
        "value": 80,
        "data_type": "int",
        "unit": "%",
        "range": {"min": 0, "max": 100},
        "required": true
      }
    ],
    "timeout_seconds": 30,
    "retry_count": 3
  },
  
  "validation": {
    "passed": true,
    "parameter_validation": true,
    "safety_check": true,
    "permission_check": true,
    "validation_timestamp": "2026-04-03T10:30:00Z"
  },
  
  "risk_assessment": {
    "risk_level": "low",
    "risk_factors": [],
    "confidence_score": 0.95,
    "assessment_timestamp": "2026-04-03T10:30:00Z"
  },
  
  "audit": {
    "proposal_id": "PROP-20260403-a1b2c3d4",
    "operator": "system",
    "agent_name": "CommandExecutionExpert",
    "session_id": "sess_12345",
    "review_summary": "指令通过安全审查，建议执行",
    "created_at": "2026-04-03T10:30:00Z"
  },
  
  "priority": 5,
  "tags": ["charge", "low-risk"]
}
```

## 使用方法

### 1. Agent 生成提案

```python
from tools.generate_proposal import generate_execution_proposal

# Agent 审查指令后生成提案
proposal_json = generate_execution_proposal(
    command_type="charge",
    device_id="dev_001",
    device_type="PCS",
    parameters={
        "power": 100.0,
        "target_soc": 80
    },
    api_endpoint="/api/v1/devices/pcs/charge",
    http_method="POST",
    validation_passed=True,
    validation_details={
        "parameter_validation": True,
        "safety_check": True,
        "permission_check": True
    },
    risk_level="low",
    review_summary="指令通过安全审查，建议执行",
    operator="system",
    session_id="sess_12345"
)
```

### 2. 业务 API 执行提案

```python
from tools.generate_proposal import parse_proposal_from_json
from schemas import ExecutionProposal

# 解析提案
response = parse_proposal_from_json(proposal_json)

if not response.success:
    return {"error": response.error}

proposal = response.proposal

# 验证签名
if not validate_proposal_signature(proposal):
    return {"error": "Invalid signature"}

# 检查安全性
if not proposal.is_safe_to_execute():
    return {"error": "Not safe to execute"}

# 转换为执行请求
execution_request = proposal.to_execution_request()

# 调用设备 API
result = await call_device_api(
    endpoint=execution_request["api_endpoint"],
    method=execution_request["http_method"],
    parameters=execution_request["parameters"]
)
```

## 文件说明

### 核心文件

- **[schemas.py](schemas.py)**: 数据模型定义
  - `ExecutionProposal`: 执行提案主模型
  - `ProposalResponse`: 提案响应格式
  - 各种辅助模型（ValidationBackcheck、RiskAssessment 等）

- **[tools/generate_proposal.py](tools/generate_proposal.py)**: 生成提案工具
  - `generate_execution_proposal`: Agent 调用的工具函数
  - `parse_proposal_from_json`: 解析 JSON 提案
  - `validate_proposal_signature`: 验证提案签名

- **[example_usage.py](example_usage.py)**: 完整使用示例
  - Agent 生成提案示例
  - 业务 API 执行提案示例
  - 完整工作流程演示

### 已有文件（保留）

- **[agent.py](agent.py)**: Agent 定义
- **[prompts.py](prompts.py)**: Agent 提示词
- **[tools/__init__.py](tools/__init__.py)**: 其他工具（审查、评估等）

## 迁移指南

### 从 `execute_device_command` 迁移

**旧方式（不推荐）**:
```python
# Agent 直接执行
result = await execute_device_command(
    command_type="charge",
    device_id="dev_001",
    parameters={"power": 100}
)
```

**新方式（推荐）**:
```python
# Step 1: Agent 生成提案
proposal_json = generate_execution_proposal(
    command_type="charge",
    device_id="dev_001",
    parameters={"power": 100},
    api_endpoint="/api/v1/devices/pcs/charge",
    validation_passed=True,
    # ... 其他参数
)

# Step 2: 返回给业务层，由业务层执行
return proposal_json
```

## 最佳实践

### 1. API 端点设计

```python
# 推荐：RESTful 风格的端点
api_endpoints = {
    "charge": "/api/v1/devices/{device_type}/charge",
    "discharge": "/api/v1/devices/{device_type}/discharge",
    "stop": "/api/v1/devices/{device_type}/stop",
    "standby": "/api/v1/devices/{device_type}/standby"
}
```

### 2. 参数验证

```python
# Agent 层：验证参数范围和类型
if power > 500:
    return generate_execution_proposal(
        validation_passed=False,
        review_summary="功率超出安全范围"
    )
```

### 3. 风险评估

```python
# Agent 层：评估风险等级
risk_level = assess_risk(
    device_health=device.soh,
    power=parameters["power"],
    duration=parameters.get("duration", 0)
)

if risk_level == "high":
    # 添加风险因素
    risk_factors = ["大功率长时间运行", "设备健康度较低"]
```

### 4. 审计日志

```python
# API 层：记录完整的审计日志
await audit_log.create({
    "proposal_id": proposal.proposal_id,
    "operator": proposal.audit.operator,
    "action": proposal.target.command_type,
    "parameters": proposal.target.parameters,
    "executed_at": datetime.now(),
    "result": "success",
    "execution_time_ms": 123
})
```

## 测试

### 测试 Agent 层

```python
def test_agent_generates_proposal():
    """测试 Agent 生成提案的逻辑"""
    proposal = generate_execution_proposal(
        command_type="charge",
        device_id="dev_001",
        # ...
    )
    
    response = parse_proposal_from_json(proposal)
    assert response.success
    assert response.proposal.validation.passed
```

### 测试 API 层

```python
async def test_api_executes_proposal():
    """测试 API 执行提案的逻辑"""
    proposal_json = load_test_proposal()
    
    api_client = DeviceAPIClient()
    result = await api_client.execute_proposal(proposal_json)
    
    assert result["success"]
    assert result["proposal_id"] == "PROP-xxx"
```

## 下一步

1. ✅ 完成数据结构设计
2. ✅ 实现提案生成工具
3. ⏳ 更新 Agent 提示词
4. ⏳ 实现 API 层执行逻辑
5. ⏳ 添加签名验证
6. ⏳ 编写单元测试
7. ⏳ 更新文档

## 相关文档

- [schemas.py API 文档](schemas.py)
- [工具使用示例](example_usage.py)
- [Agent 定义](agent.py)
