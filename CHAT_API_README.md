# EMS Chat API 使用指南

## 接口概述

本项目提供两个对话接口：
- **流式接口** (`/projectApi/chat/stream`) - Server-Sent Events 实时输出
- **普通接口** (`/projectApi/chat`) - 等待完整回复后返回

---

## 快速开始

### 1. 启动服务

```bash
# 方式 1: 使用 uvicorn 直接启动
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 使用脚本启动（如果有启动脚本）
./start.sh
```

### 2. 测试接口

```bash
# 运行测试脚本
python test_chat_api.py
```

---

## API 接口详情

### 1. 流式对话接口 (推荐)

**端点**: `POST /projectApi/chat/stream`

**请求示例**:

```bash
curl -X POST "http://localhost:8000/projectApi/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "搜索最新的江苏分时电价政策",
    "user_id": "user_001",
    "stream": true
  }'
```

**Python 调用示例**:

```python
import requests
import json

url = "http://localhost:8000/projectApi/chat/stream"
payload = {
    "message": "江苏分时电价政策",
    "user_id": "user_001"
}

response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line.startswith(b"data: "):
        data = json.loads(line[6:])
        print(data)
```

**响应格式 (SSE)**:

```
data: {"type": "metadata", "metadata": {"session_id": "session_abc123"}}

data: {"type": "token", "content": "江苏省的分时电价政策..."}

data: {"type": "done", "metadata": {"elapsed_time": 15.6}}
```

**字段说明**:
- `type: metadata` - 元数据（会话ID等）
- `type: token` - AI 回复内容片段
- `type: done` - 对话完成
- `type: error` - 错误信息

---

### 2. 普通对话接口

**端点**: `POST /projectApi/chat`

**请求示例**:

```bash
curl -X POST "http://localhost:8000/projectApi/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "江苏分时电价有哪些时段？",
    "user_id": "user_001"
  }'
```

**响应示例**:

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "response": "江苏省分时电价分为高峰、低谷、平段...",
    "session_id": "session_abc123",
    "message": "江苏分时电价有哪些时段？"
  }
}
```

---

### 3. 多轮对话

**使用相同的 `session_id` 实现上下文记忆**:

```python
# 第一轮
response1 = requests.post(url, json={
    "message": "江苏的分时电价政策是什么？",
    "user_id": "user_001"
})
session_id = response1.json()['data']['session_id']

# 第二轮（带 session_id）
response2 = requests.post(url, json={
    "message": "具体有哪些时段？",  # 会理解"时段"指代上一轮的江苏电价
    "user_id": "user_001",
    "session_id": session_id
})
```

---

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `message` | string | ✅ | 用户消息内容 (1-5000 字) |
| `user_id` | string | ❌ | 用户ID，默认 "default_user" |
| `session_id` | string | ❌ | 会话ID，用于多轮对话 |
| `stream` | boolean | ❌ | 是否流式输出，默认 true |

---

## 功能特性

✅ **多 Agent 协作** - 自动调用储能、电力、搜索等领域专家
✅ **实时搜索** - 集成 Tavily 搜索引擎获取最新政策
✅ **上下文记忆** - 自动保存对话历史（最近 20 条）
✅ **用户档案** - 自动归档用户偏好和业务背景
✅ **流式输出** - SSE 实时推送 AI 回复
✅ **错误处理** - 完善的异常捕获和错误提示

---

## 性能优化

已实施优化：
- ✅ 使用 `glm-4-flash` 模型（快速响应）
- ✅ 精准搜索策略（减少重复搜索）
- ✅ `basic` 搜索深度（平衡速度和质量）
- ✅ 单次综合搜索（避免多轮查询）

**当前性能**:
- 平均响应时间: 15-25 秒
- Token 消耗: ~11,000
- 搜索次数: 1-2 次

---

## 前端集成示例

### JavaScript/TypeScript

```typescript
async function streamChat(message: string, sessionId?: string) {
  const response = await fetch('http://localhost:8000/projectApi/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId })
  });

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'token') {
          console.log(data.content); // 实时输出
        }
      }
    }
  }
}
```

---

## 故障排查

### 问题 1: 连接失败
```
❌ Connection refused
```
**解决**: 确保服务已启动 `uv run uvicorn src.main:app --reload`

### 问题 2: 响应慢
**原因**: Agent 需要搜索和多次 LLM 调用
**优化**: 已自动优化，首次响应约 2-5 秒

### 问题 3: 没有上下文记忆
**解决**: 确保多轮对话使用相同的 `session_id`

---

## 技术架构

```
前端 → FastAPI Router → ChatService → EMS Agent
                              ↓
                         WorkspaceManager
                              ↓
                         User Profile (JSON)
```

**核心组件**:
- `router.py` - API 路由和 SSE 处理
- `service.py` - ChatAgentService 业务逻辑
- `factory.py` - Agent 创建和配置
- `workspace.py` - 用户会话和档案管理

---

## 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SSE 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [deepagents 文档](https://github.com/deepagents-ai)

---

## 联系支持

如有问题，请查看项目 README 或提交 Issue。
