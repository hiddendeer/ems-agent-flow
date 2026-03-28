# EMS MCP 服务使用指南

## 📋 目录
- [快速开始](#快速开始)
- [配置方式](#配置方式)
- [测试工具](#测试工具)
- [智能体调用示例](#智能体调用示例)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd f:/AI_INFO/ems-agent-flow

# 安装 fastmcp
pip install fastmcp
```

### 2. 启动服务

```bash
# 方式一：直接运行（stdio 模式）
python src/mcp/server.py

# 方式二：使用 MCP Inspector 测试（推荐）
npx -y @modelcontextprotocol/inspector python src/mcp/server.py
```

---

## ⚙️ 配置方式

### 方式一：Claude Desktop（推荐）

#### Windows 配置路径
```
C:\Users\<你的用户名>\AppData\Roaming\Claude\claude_desktop_config.json
```

#### 配置内容
```json
{
  "mcpServers": {
    "ems_manager": {
      "command": "python",
      "args": [
        "f:/AI_INFO/ems-agent-flow/src/mcp/server.py"
      ],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

#### 重启 Claude Desktop
配置完成后，完全退出并重新启动 Claude Desktop。

#### 验证连接
在 Claude Desktop 中输入：
```
我想要管理设备，你能帮我吗？
```

Claude 应该会自动调用 `list_manageable_entities` 工具。

---

### 方式二：在代码中使用 MCP 客户端

如果你有自己的智能体代码，可以使用 MCP SDK：

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 创建服务器参数
server_params = StdioServerParameters(
    command="python",
    args=["f:/AI_INFO/ems-agent-flow/src/mcp/server.py"],
    env={"API_BASE_URL": "http://localhost:8000"}
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()

            # 列出可用工具
            tools = await session.list_tools()
            print("可用工具:", [t.name for t in tools.tools])

            # 调用工具
            result = await session.call_tool("list_manageable_entities", {})
            print(result.content[0].text)

# 运行
import asyncio
asyncio.run(main())
```

---

## 🧪 测试工具

### 使用 MCP Inspector（强烈推荐）

MCP Inspector 是官方提供的交互式测试工具：

```bash
# 安装 Node.js（如果没有）
# 然后运行：
npx -y @modelcontextprotocol/inspector python src/mcp/server.py
```

这会打开一个 Web 界面，你可以：
- 📋 查看所有可用工具
- 🎯 手动测试每个工具
- 📝 查看工具的输入/输出
- 🔍 调试 MCP 通信

### 命令行测试脚本

创建测试脚本 `test_mcp.py`：

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp():
    server_params = StdioServerParameters(
        command="python",
        args=["src/mcp/server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 测试 1: 列出实体
            print("\n=== 测试 1: 列出可管理实体 ===")
            result = await session.call_tool("list_manageable_entities", {})
            print(result.content[0].text)

            # 测试 2: 获取字段
            print("\n=== 测试 2: 获取设备字段 ===")
            result = await session.call_tool("get_entity_fields", {
                "entity_name": "device"
            })
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_mcp())
```

运行测试：
```bash
python test_mcp.py
```

---

## 🤖 智能体调用示例

### 示例 1：Claude Desktop 对话

```
用户: 我想要添加一个新的电池设备

Claude:
[自动调用 list_manageable_entities]
我发现系统支持管理设备。

[自动调用 get_entity_fields]
要添加设备，需要以下信息：
- device_name: 设备名称
- device_type: 设备类型（BATTERY/PCS/METER）
- serial_number: 序列号
- capacity_kwh: 容量（可选）

请提供这些信息，我来帮你创建。

用户: 设备名称是1号电池组，类型是BATTERY，序列号是SN001，容量500kWh

Claude:
[自动调用 create_record]
✅ 设备已成功创建！
```

### 示例 2：程序化调用

```python
# 智能体代码
async def create_device_with_agent(agent, device_info):
    """智能体创建设备的完整流程"""

    # 1. 获取可管理实体
    entities = await agent.call_tool("list_manageable_entities")
    print("系统支持:", entities)

    # 2. 获取字段结构
    schema = await agent.call_tool("get_entity_fields", {
        "entity_name": "device"
    })

    # 3. 验证数据
    required_fields = schema["required"]
    for field in required_fields:
        if field not in device_info:
            raise ValueError(f"缺少必填字段: {field}")

    # 4. 创建记录
    result = await agent.call_tool("create_record", {
        "entity_name": "device",
        "record_data": device_info
    })

    return result

# 使用
device_data = {
    "device_name": "1号电池组",
    "device_type": "BATTERY",
    "serial_number": "SN001",
    "capacity_kwh": 500
}

result = await create_device_with_agent(agent, device_data)
```

---

## 🔧 环境变量配置

创建 `.env` 文件（在项目根目录）：

```bash
# 后端 API 地址
API_BASE_URL=http://localhost:8000

# 可选：其他配置
LOG_LEVEL=INFO
```

在 `server.py` 中已自动加载：
```python
from dotenv import load_dotenv
load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
```

---

## 📊 工具列表

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `list_manageable_entities` | 列出可管理实体 | 无 |
| `get_entity_fields` | 获取实体字段定义 | `entity_name` |
| `list_records` | 查询记录列表 | `entity_name` |
| `get_record_detail` | 获取记录详情 | `entity_name`, `record_id` |
| `create_record` | 创建新记录 | `entity_name`, `record_data` |
| `update_record` | 更新记录 | `entity_name`, `record_id`, `updated_fields` |

---

## 🐛 故障排查

### 问题 1：Claude Desktop 看不到工具

**检查清单：**
- ✅ 配置文件路径是否正确
- ✅ JSON 格式是否正确（注意逗号）
- ✅ Python 路径是否正确
- ✅ 是否完全重启了 Claude Desktop

**调试方法：**
```bash
# 手动测试服务是否能启动
python src/mcp/server.py
```

### 问题 2：工具调用失败

**检查日志：**
```bash
# 使用 verbose 模式
python src/mcp/server.py --verbose
```

**常见原因：**
- Schema 文件不存在或格式错误
- 后端 API 未启动
- 环境变量未配置

### 问题 3：返回数据格式错误

**验证 Schema：**
```bash
# 使用 JSON 验证工具
python -m json.tool src/mcp/schemas/device.json
```

---

## 📚 相关资源

- [MCP 官方文档](https://modelcontextprotocol.io)
- [fastmcp 文档](https://github.com/jlowin/fastmcp)
- [Claude Desktop 配置指南](https://docs.anthropic.com/claude/docs/mcp)

---

## 🎯 下一步

1. ✅ 安装依赖
2. ✅ 配置 Claude Desktop
3. ✅ 使用 MCP Inspector 测试
4. ✅ 在对话中尝试创建设备
5. ✅ 补充真实的 HTTP 接口调用

需要帮助实现真实 HTTP 调用吗？
