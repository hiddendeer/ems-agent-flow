"""
测试 Chat API 接口

演示如何调用流式和非流式对话接口
"""

import requests
import json


def test_stream_chat():
    """测试流式对话接口 (SSE)"""
    print("=" * 60)
    print("测试流式对话接口 (SSE)")
    print("=" * 60)

    url = "http://localhost:8000/projectApi/chat/stream"

    payload = {
        "message": "搜索最新的江苏分时电价政策",
        "user_id": "test_user_001",
        "stream": True
    }

    print(f"\n📤 请求: {json.dumps(payload, ensure_ascii=False)}")
    print("\n📥 响应流:\n")

    try:
        response = requests.post(url, json=payload, stream=True, timeout=300)

        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data = json.loads(line_str[6:])  # 去掉 "data: " 前缀

                        if data['type'] == 'metadata':
                            print(f"📋 [元数据] {data.get('metadata')}")
                        elif data['type'] == 'token':
                            content = data.get('content', '')
                            print(f"💬 [内容片段] {content[:100]}...")
                        elif data['type'] == 'done':
                            print(f"\n✅ [完成] 耗时: {data.get('metadata', {}).get('elapsed_time', 0):.2f}秒")
                        elif data['type'] == 'error':
                            print(f"❌ [错误] {data.get('error')}")

            print("\n✅ 流式测试完成")
        else:
            print(f"❌ HTTP 错误: {response.status_code}")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！请确保 FastAPI 服务已启动:")
        print("   uv run uvicorn src.main:app --reload")
    except Exception as e:
        print(f"❌ 错误: {e}")


def test_normal_chat():
    """测试非流式对话接口"""
    print("\n" + "=" * 60)
    print("测试非流式对话接口")
    print("=" * 60)

    url = "http://localhost:8000/projectApi/chat"

    payload = {
        "message": "江苏分时电价有哪些时段？",
        "user_id": "test_user_001",
        "stream": False
    }

    print(f"\n📤 请求: {json.dumps(payload, ensure_ascii=False)}")

    try:
        response = requests.post(url, json=payload, timeout=300)

        print(f"\n📥 状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 响应:")
            print(f"   消息: {result.get('message')}")
            print(f"   Session ID: {result.get('data', {}).get('session_id')}")
            print(f"\n📝 完整回复:")
            print(result.get('data', {}).get('response', '')[:500] + "...")
        else:
            print(f"❌ 错误响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！请确保 FastAPI 服务已启动")
    except Exception as e:
        print(f"❌ 错误: {e}")


def test_multi_turn_chat():
    """测试多轮对话"""
    print("\n" + "=" * 60)
    print("测试多轮对话")
    print("=" * 60)

    url = "http://localhost:8000/projectApi/chat"

    # 第一轮对话
    print("\n📤 第一轮: 询问江苏电价")
    payload1 = {
        "message": "江苏的分时电价政策是什么？",
        "user_id": "test_user_002"
    }

    try:
        response1 = requests.post(url, json=payload1, timeout=300)
        if response1.status_code == 200:
            result1 = response1.json()
            session_id = result1.get('data', {}).get('session_id')
            print(f"✅ Session ID: {session_id}")

            # 第二轮对话（使用相同的 session_id）
            print("\n📤 第二轮: 基于上下文追问")
            payload2 = {
                "message": "具体有哪些时段？",
                "user_id": "test_user_002",
                "session_id": session_id
            }

            response2 = requests.post(url, json=payload2, timeout=300)
            if response2.status_code == 200:
                result2 = response2.json()
                print(f"✅ 回复: {result2.get('data', {}).get('response', '')[:200]}...")

    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    # 运行测试
    test_normal_chat()
    test_stream_chat()
    test_multi_turn_chat()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
