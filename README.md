# EMS Agent Flow 🌍🔋

> **智能能源管理系统 (EMS) 的多 Agent 协作架构 — 基于深度智能体的下一代能源管理平台**

这是一套基于 `deepagents` 框架构建的企业级多 Agent 协作系统，专为新能源储能电站、电力市场交易和虚拟电厂 (VPP) 运营设计。系统通过多个专业领域智能体的协同工作，实现从政策分析、市场策略到设备控制的全链路智能决策。

---

## 🎯 核心价值

**为新能源企业打造的 AI 决策中枢**

| 角色 | 痛点 | 系统解决方案 |
|------|------|------------|
| 🏢 **储能电站运营方** | 充放电策略需人工反复计算，峰谷套利收益优化难 | **储能专家智能体** - 实时分析电价，自动生成最优充放电策略 |
| 📊 **电力市场交易员** | 政策文件密密麻麻，找不到影响盈亏的关键条款 | **市场分析智能体** - 自动检索政策文件，提炼决策要点 |
| 🔬 **VPP 投资负责人** | 储能接入方案需要对潮流、调度进行仿真验证 | **建模优化智能体** - 基于 PyPSA 进行运筹优化求解 |
| ⚡ **系统运维工程师** | 设备指令执行缺乏安全保障，操作风险高 | **指令执行智能体** - 多层安全审查，完整审计日志 |
| 🕵️ **市场情报分析师** | 竞争对手动态和市场趋势需要专人盯盘 | **搜索智能体** - 24/7 自动追踪行业动态和政策变化 |

---

## 🧠 系统架构

### 多层智能体协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Lead Agent (首席协调官)                   │
│              • 任务分解与并行派发                            │
│              • 跨领域结果整合                                │
│              • 用户长期记忆管理                              │
└─────────────┬───────────────────────────────────────────────┘
              │
      ┌───────┴───────┬───────────┬───────────┬───────────┐
      │               │           │           │           │
      ▼               ▼           ▼           ▼           ▼
┌──────────┐   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│储能运营  │   │电力市场  │  │情报搜索  │  │系统规划  │  │指令执行  │
│专家智能体│   │分析智能体│  │智能体    │  │优化智能体│  │智能体    │
└──────────┘   └──────────┘  └──────────┘  └──────────┘  └──────────┘
      │               │           │           │           │
      ▼               ▼           ▼           ▼           ▼
BMS/PCS控制    分时电价查询   Tavily搜索   PyPSA建模   安全审查执行
SOC优化        需求响应       政策文件检索  经济调度     审计日志
峰谷套利计算   市场预测       竞对分析     基础设施规划  紧急控制
```

### 核心设计特性

**🚀 极速响应架构**
- 采用并行任务派发策略，典型任务在 13 秒内完成
- 后台异步复盘机制，不阻塞主流程
- 智能缓存和增量更新

**🔒 企业级安全保障**
- `CrossPlatformPathMiddleware` - 跨平台路径自动修正
- `@timeout_fallback` - 工具执行超时熔断保护
- 多层指令审查机制（参数验证、安全检查、权限确认）
- 完整操作审计日志

**🧠 智能记忆系统**
- 用户偏好自动学习
- 业务参数持久化存储
- 跨会话上下文保持

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **Agent 编排** | [deepagents](https://github.com/deepinsight/deepagents) | LangGraph 多 Agent 协作框架 |
| **Web 框架** | FastAPI + Uvicorn | 高性能异步 API 服务 |
| **LLM 接入** | OpenAI API | 兼容 GLM-4、GPT-4 等模型 |
| **实时搜索** | Tavily AI | 真实互联网搜索接入 |
| **优化建模** | PyPSA + HiGHS | 线性规划求解器 |
| **时序数据库** | InfluxDB | 电力设备数据存储 |
| **工业协议** | Modbus | PLC/BMS 设备通信 |
| **MCP 协议** | fastmcp | 模型上下文协议集成 |
| **数据验证** | Pydantic | 类型安全的数据模型 |
| **数据库** | SQLite/MySQL | 支持 SQLite 和 MySQL |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/hiddendeer/ems-agent-flow.git
cd ems-agent-flow

# Python 版本要求: >= 3.11
python --version
```

### 2. 安装依赖

```bash
# 推荐：使用 uv (超快包管理器)
pip install uv
uv sync

# 或使用传统 pip
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入必要配置
# 必须配置的项：
# - OPENAI_API_KEY: 你的 API 密钥
# - OPENAI_API_BASE: API 基础 URL
# - TAVILY_API_KEY: Tavily 搜索密钥
# - INFLUXDB_TOKEN: 时序数据库凭证
```

### 4. 启动服务

```bash
# 方式一：启动 FastAPI 后端服务
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 方式二：运行多 Agent 协作演示
uv run python -m src.agents.demo.multi_agent_demo

# 方式三：启动 MCP 服务（用于 Claude Desktop 集成）
uv run python src/mcp/server.py
```

### 5. 验证安装

```bash
# 访问 API 文档
http://localhost:8000/docs

# 健康检查
curl http://localhost:8000/health
```

---

## 💡 使用示例

### 示例一：储能电站智能调度

```
用户: 调研江苏省最新的工业电价政策，并制定储能系统的最优充放电策略。

系统响应 (约 13 秒):
✅ 已获取江苏峰谷电价数据
   - 峰段: 1.05 元/kWh (08:00-12:00, 17:00-21:00)
   - 谷段: 0.28 元/kWh (00:00-08:00, 12:00-17:00)

✅ 最优充放电策略已生成
   - 充电时间: 00:00-08:00 (8小时)
   - 放电时间: 08:00-12:00 + 17:00-21:00 (8小时)
   - 静置时间: 21:00-24:00 (3小时)

✅ 收益预估
   - 日收益: 672 元
   - 月收益: 20,160 元
   - 年收益: 245,280 元
   - 静态回收期: 3.2 年
```

### 示例二：政策情报自动搜索

```
用户: 搜索最新的中国分时电价政策，分析对储能项目的影响。

系统响应 (约 45 秒):
✅ 搜索到 12 篇相关政策文件
✅ 核心发现:
   - 政策趋势: 从规模扩张转向价值深耕
   - 关键变化: 峰谷价差扩大到 0.77 元/kWh
   - 储能利好: 需求响应补贴最高 100 元/kW

✅ 对项目的影响分析
   - 收益模型: IRR 预计提升 2-3 个百分点
   - 建议调整: 增加需求响应模块
   - 风险提示: 部分地区峰段时长缩短
```

### 示例三：设备指令安全执行

```
用户: 向 1 号电池组下发充电指令，功率 500kW，目标 SOC 80%。

系统响应 (约 3 秒):
✅ 指令审查通过
   - 参数验证: ✓ 功率在额定范围内
   - 安全检查: ✓ 电池温度正常，无故障
   - 权限确认: ✓ 操作员有权限

✅ 风险评估: 低风险
   - 健康度: 92% (良好)
   - 经济性: 建议执行 (当前电价 0.35 元/kWh)

✅ 指令已下发
   - 设备: 1 号电池组 (dev_001)
   - 指令: 充电 500kW → SOC 80%
   - 预计时间: 48 分钟

✅ 操作日志已记录 (ID: CMD_20250329_001)
```

---

## 🏗️ 项目结构

```
ems-agent-flow/
├── src/
│   ├── agents/                 # 智能体模块
│   │   ├── core/              # 核心框架
│   │   │   ├── domain_agent.py    # 领域智能体基类
│   │   │   ├── factory.py         # 智能 EM S 工厂
│   │   │   ├── registry.py        # 智能体注册中心
│   │   │   ├── workspace.py       # 工作区和记忆管理
│   │   │   └── resilience.py      # 韧性中间件
│   │   ├── domains/           # 领域智能体
│   │   │   ├── command_execution/  # 指令执行智能体
│   │   │   ├── energy_storage/     # 储能运营智能体
│   │   │   ├── power/              # 电力市场智能体
│   │   │   ├── pypsa_modeling/     # 系统规划智能体
│   │   │   └── search/             # 情报搜索智能体
│   │   └── demo/              # 演示和测试
│   ├── common/                # 公共模块
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库连接
│   │   └── exceptions.py        # 异常处理
│   ├── crud/                  # 数据库 CRUD
│   ├── mcp/                   # MCP 协议服务
│   │   ├── server.py           # MCP 服务器
│   │   └── schemas/            # 实体 Schema 定义
│   ├── projectApi/            # 项目业务 API
│   ├── influxApi/             # InfluxDB 接口
│   ├── iecApi/                # IEC 协议接口
│   ├── utils/                 # 工具类
│   └── main.py                # FastAPI 应用入口
├── workspaces/                # 用户工作区
│   └── user_*/                # 个性化数据和记忆
├── docs/                      # 文档
├── tests/                     # 测试
├── pyproject.toml            # 项目配置
├── requirements.txt          # 依赖清单
├── .env.example              # 环境变量模板
└── README.md                 # 本文件
```

---

## 🔌 扩展开发

### 新增领域智能体

只需 4 步即可添加新的专家智能体：

1. **创建智能体目录**
   ```bash
   mkdir src/agents/domains/your_expert
   ```

2. **实现智能体类**
   ```python
   # src/agents/domains/your_expert/agent.py
   from ...core.domain_agent import DomainAgent
   from ...core.registry import AgentRegistry

   class YourExpertAgent(DomainAgent):
       def __init__(self):
           super().__init__(
               name="YourExpert",
               description="你的专家描述..."
           )

       def get_tools(self):
           return [your_tool_1, your_tool_2]

       def get_system_prompt(self):
           return "你的提示词..."

   # 注册智能体
   AgentRegistry.register(YourExpertAgent())
   ```

3. **创建工具集**
   ```python
   # src/agents/domains/your_expert/tools/__init__.py
   from langchain_core.tools import tool

   @tool
   def your_expert_tool(param: str) -> str:
       \"\"\"工具描述\"\"\"
       return "执行结果"
   ```

4. **在 __init__.py 中导入**
   ```python
   # src/agents/domains/__init__.py
   def register_all_domains():
       from . import your_expert  # 新增
       # ...
   ```

系统会在下次启动时自动发现并集成新智能体。

---

## 🔧 配置说明

### 核心配置项 (.env)

```bash
# ========== 应用配置 ==========
APP_NAME="FastAPI EMS"
DEBUG=false
ENVIRONMENT=development  # development | staging | production

# ========== LLM 配置 ==========
OPENAI_API_KEY=your_key_here
OPENAI_API_BASE=https://open.bigmodel.cn/api/coding/paas/v4
DEFAULT_MODEL=openai:glm-4.0

# ========== 搜索服务 ==========
TAVILY_API_KEY=your_tavily_key

# ========== 数据库配置 ==========
DB_TYPE=sqlite  # sqlite | mysql
DB_URL=sqlite+aiosqlite:///./ems.db

# ========== InfluxDB 配置 ==========
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token_here
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=battery_data

# ========== API 服务 ==========
API_V1_PREFIX=/api/v1
HOST=0.0.0.0
PORT=8000
```

---

## 📚 文档资源

- **[MCP 服务集成指南](src/mcp/README.md)** - Claude Desktop 集成教程
- **[LangChain 1.0 教程](docs/langchain-1.0-tutorial.md)** - LangChain 使用指南
- **[Redis 基础](docs/redis-basics.md)** - 缓存数据库使用
- **[代码审查报告](docs/CODE_REVIEW_2026_03_29.md)** - 最近的质量优化记录

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出改进建议！

### 开发规范

1. **代码风格**: 遵循 PEP 8，使用 `ruff` 进行格式化
2. **提交规范**: 使用 Conventional Commits 格式
3. **测试要求**: 新功能需包含单元测试
4. **文档更新**: 重要变更需更新相关文档

### Pull Request 流程

1. Fork 项目到你的 GitHub
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🌟 致谢

本项目基于以下优秀的开源项目：

- [deepagents](https://github.com/deepinsight/deepagents) - 多 Agent 协作框架
- [LangChain](https://github.com/langchain-langchain/langchain) - LLM 应用开发框架
- [FastAPI](https://github.com/tiangolo/fastapi) - 高性能 Web 框架
- [PyPSA](https://github.com/PyPSA/PyPSA) - 电力系统分析工具包

---

## 📞 联系方式

- **GitHub Issues**: 报告问题和功能请求
- **项目主页**: [https://github.com/hiddendeer/ems-agent-flow](https://github.com/hiddendeer/ems-agent-flow)

---

> **"通过 AI 赋能，让每一度电都创造最大的经济价值。"** ⚡
