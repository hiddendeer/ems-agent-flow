"""
文件系统写入路径验证脚本 — 模拟 Agent 行为直接测试。
不消耗 LLM Token。
"""

import os
import asyncio
from src.agents.core.factory import CrossPlatformPathMiddleware

# 模拟 FilesystemBackend 的行为
class MockHandler:
    def __init__(self, root):
        self.root = root
        
    def __call__(self, request):
        path = request.args.get("path")
        # 模拟 deepagents 的 write_file 合并路径逻辑
        # 在 Windows 上，如果 path 以 / 开头，os.path.join(root, "/src") 会变成 "E:/src"
        final_path = os.path.join(self.root, path)
        print(f"🎬 [Mock Execution]: 尝试写入物理路径 -> {final_path}")
        
        # 真正创建目录并写入，验证权限和位置
        os.makedirs(os.path.dirname(final_path), exist_ok=True)
        with open(final_path, "w", encoding="utf-8") as f:
            f.write("This is a test content from FS Verification script.")
        
        return f"Successfully wrote to {path}"

class MockRequest:
    def __init__(self, name, args):
        self.name = name
        self.args = args

async def test_path_fix():
    print(f"\n{'='*60}")
    print("🧪 [FS 路径修正测试开始]")
    print(f"{'='*60}")
    
    project_root = os.path.abspath(os.getcwd())
    print(f"📁 当前项目根目录: {project_root}")
    
    mw = CrossPlatformPathMiddleware()
    handler = MockHandler(project_root)
    
    # 情况 A: 带有“幻觉”斜杠的路径（Agent 最容易出现的错误）
    bad_path = "/src/agents/reports/test_with_slash.txt"
    print(f"\n🔍 [Case A] 模拟 Agent 传入错误路径: '{bad_path}'")
    
    req_a = MockRequest("write_file", {"path": bad_path})
    
    # 模拟异步拦截
    result_a = await mw.awrap_tool_call(req_a, handler)
    print(f"✅ 执行结果: {result_a}")
    
    # 情况 B: 正常相对路径
    good_path = "src/agents/reports/test_correct_relative.txt"
    print(f"\n🔍 [Case B] 模拟 Agent 传入正确相对路径: '{good_path}'")
    req_b = MockRequest("write_file", {"path": good_path})
    result_b = await mw.awrap_tool_call(req_b, handler)
    print(f"✅ 执行结果: {result_b}")

    print(f"\n{'='*60}")
    print("📈 [结果验证]")
    
    expected_dir = os.path.join(project_root, "src/agents/reports")
    print(f"检查目录: {expected_dir}")
    
    if os.path.exists(expected_dir):
        files = os.listdir(expected_dir)
        print(f"发现文件: {files}")
    else:
        print("❌ 错误：指定目录仍未创建！")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    asyncio.run(test_path_fix())
