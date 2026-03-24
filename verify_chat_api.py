"""
快速验证 Chat API 是否可用

检查接口是否正确注册
"""

import requests


def test_api_docs():
    """测试 API 文档是否可访问"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API 文档可访问: http://localhost:8000/docs")
            return True
        else:
            print(f"❌ API 文档返回状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务！请先启动:")
        print("   uv run uvicorn src.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


def test_health():
    """测试健康检查接口"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务健康: {data.get('app')} v{data.get('version')}")
            return True
        return False
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def test_chat_endpoint():
    """测试 Chat 接口是否注册"""
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi = response.json()
            paths = openapi.get("paths", {})

            chat_endpoints = [
                "/api/v1/projectApi/chat/stream",
                "/api/v1/projectApi/chat"
            ]

            for endpoint in chat_endpoints:
                if endpoint in paths:
                    print(f"✅ 接口已注册: POST {endpoint}")
                else:
                    print(f"❌ 接口未找到: {endpoint}")

            return len([e for e in chat_endpoints if e in paths]) == len(chat_endpoints)
        return False
    except Exception as e:
        print(f"❌ 检查接口失败: {e}")
        return False


def test_simple_chat():
    """简单的对话测试（非流式）"""
    print("\n" + "=" * 60)
    print("执行简单的对话测试...")
    print("=" * 60)

    try:
        response = requests.post(
            "http://localhost:8000/api/v1/projectApi/chat",
            json={"message": "你好", "user_id": "test"},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 对话成功!")
            print(f"   Session ID: {result.get('data', {}).get('session_id')}")
            return True
        else:
            print(f"❌ 对话失败: {response.status_code}")
            print(f"   {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("⏱️  请求超时（这是正常的，Agent 需要时间处理）")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Chat API 验证脚本")
    print("=" * 60 + "\n")

    # 运行测试
    results = []
    results.append(test_api_docs())
    results.append(test_health())
    results.append(test_chat_endpoint())

    # 如果前面的测试都通过，执行简单对话测试
    if all(results):
        print("\n" + "=" * 60)
        print("所有基础检查通过！")
        print("=" * 60)
        test_simple_chat()
    else:
        print("\n" + "=" * 60)
        print("请确保服务已正确启动！")
        print("=" * 60)
        print("启动命令: uv run uvicorn src.main:app --reload")
