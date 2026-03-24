"""
EMS 智能对话 API 路由
提供基于多 Agent 系统的流式对话接口
"""
import json

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from src.common.schemas import ResponseModel
from src.projectApi.schemas import ChatRequest
from src.projectApi.service import chat_service

# 初始化路由
router = APIRouter(prefix="/projectApi", tags=["EMS 智能对话"])


# ==========================================
# SSE 流式转换辅助函数
# ==========================================

async def _generate_sse_chunks(chat_generator):
    """
    将 Agent 的流式输出转换为 SSE (Server-Sent Events) 格式

    SSE 格式: data: <json>\n\n
    """
    async for chunk in chat_generator:
        chunk_json = json.dumps(chunk, ensure_ascii=False)
        yield f"data: {chunk_json}\n\n"


# ==========================================
# 对话接口
# ==========================================

@router.post(
    "/chat/stream",
    summary="流式对话接口 (SSE)",
    description="""
支持流式回复的多轮对话接口，基于 EMS 多 Agent 系统。

**特性：**
- Server-Sent Events (SSE) 流式输出
- 多轮对话上下文管理
- 自动归档用户偏好
- 支持多 Agent 协作

**返回格式：**
- `type: metadata` - 元数据（如 session_id）
- `type: token` - AI 回复内容片段
- `type: done` - 对话完成
- `type: error` - 错误信息

**使用示例：**

```python
import requests

response = requests.post(
    "http://localhost:8000/projectApi/chat/stream",
    json={"message": "查询江苏分时电价政策", "stream": True},
    stream=True
)

for line in response.iter_lines():
    if line.startswith(b"data: "):
        data = json.loads(line[6:])
        print(data)
```
""",
)
async def chat_stream_endpoint(
    request: ChatRequest = Body(..., description="聊天请求"),
):
    """
    流式对话接口

    通过 SSE 协议实时返回 AI 生成的回复内容
    """
    async def stream_generator():
        try:
            async for chunk in chat_service.chat_stream(
                message=request.message,
                session_id=request.session_id,
                user_id=request.user_id or "default_user"
            ):
                yield chunk
        except Exception as e:
            yield {
                "type": "error",
                "error": f"内部错误: {str(e)}",
                "session_id": request.session_id
            }

    return StreamingResponse(
        _generate_sse_chunks(stream_generator()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post(
    "/chat",
    summary="普通对话接口 (非流式)",
    description="""
非流式的对话接口，等待完整回复后返回。
适合不需要实时输出的场景。
""",
)
async def chat_endpoint(
    request: ChatRequest = Body(..., description="聊天请求"),
):
    """
    非流式对话接口

    等待完整回复后一次性返回
    """
    full_response = ""
    session_id = request.session_id

    try:
        async for chunk in chat_service.chat_stream(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id or "default_user"
        ):
            if chunk["type"] == "token":
                full_response += chunk.get("content", "")
            elif chunk["type"] == "error":
                return ResponseModel(
                    code=500,
                    message="对话失败",
                    data={"error": chunk.get("error")}
                )
            elif chunk["type"] == "metadata":
                if chunk.get("metadata", {}).get("session_id"):
                    session_id = chunk["metadata"]["session_id"]

        return ResponseModel(
            code=200,
            message="success",
            data={
                "response": full_response,
                "session_id": session_id,
                "message": request.message
            }
        )

    except Exception as e:
        return ResponseModel(
            code=500,
            message=str(e),
            data=None
        )
