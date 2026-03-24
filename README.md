# EMS Agent Flow 🌍🔋

> **智能能源管理系统 (EMS) 的多 Agent 协作架构 — 4 位"数字专家"实时协作，从信息到决策最快 13 秒**

这是一套深度集成了电力领域专业知识的多 Agent 协作系统。它不只是自动化工具，而是一支懂政策、会建模、能算收益的**数字化专家团队**。

---

## 🎯 为什么新能源企业需要它？

如果您是储能电站运营方、电力市场交易员或 VPP 投资负责人，系统能帮您解决：

| 痛点 | 系统的解法 |
|------|-----------|
| 政策文件密密麻麻，找不到影响盈亏的关键条款 | **PowerSearchExpert** 自动检索 + 提炼决策摘要 |
| 充放电计划需人工反复计算峰谷套利 | **EnergyStorageExpert** 直接给出每日收益预估方案 |
| 储能接入方案需要对潮流、调度进行仿真验证 | **PyPSAModelingExpert** 运筹优化求解，量化到 kWh |
| 实时电价查询与竞争对手动态需要专人盯盘 | **PowerMarketExpert** 全天候自动追踪 |

---

## 🧠 核心架构：Lead + 4 位专家

系统模拟了"首席协调官 + 专家团队"的真实决策流程：

```
用户指令
    │
    ▼
Lead Agent（首席协调官）
├── 任务分解 & 并行派发
│
├── EnergyStorageExpert（储能运营顾问）
│     └── 工具: BMS状态查询 / PCS控制 / SOC优化 / 峰谷套利计算
│
├── PowerMarketExpert（电力市场分析师）
│     └── 工具: 分时电价查询 / 需求响应收益估算 / 电网实时状态
│
├── PowerSearchExpert（电力情报搜索员）
│     └── 工具: Tavily 实时政策搜索 / 行业研报扫描 / 竞对动态追踪
│
└── PyPSAModelingExpert（系统规划与调度优化师）
      └── 工具: 经济调度求解 / 多期基础设施长期规划
```

> **特性：** 系统采用**极速响应模式**，鼓励 Lead Agent 一次性并行派发任务，而不是串行等待。典型任务（储能套利策略+政策调研）可在 **13 秒** 内完成协作并输出结论。

---

## 💡 典型场景演示

### 场景一：储能电站的智能充放电策略

```
用户: 调研江苏省最新的工业电价政策，并制定储能系统的最优充放电策略，包括峰谷套利收益预估。

系统输出（约 13 秒）:
✅ 获取江苏峰谷电价（峰段 1.05 元/kWh，低谷 0.28 元/kWh）
✅ 充放电策略: 低谷 00:00-08:00 充电，峰段 10:00-15:00 放电
✅ 2000kWh 系统日收益 672 元 / 月度 20,160 元 / 年度 245,280 元
```

### 场景二：实时政策情报搜索

```
用户: 搜索最新的江苏分时电价政策。

系统输出（约 45 秒，含 Tavily 真实互联网搜索）:
✅ 调取真实政策文件链接与摘要
✅ 解读分时电价对储能项目静态回收期的影响
✅ 汇总 2025 年储能政策从规模扩张转向价值深耕的核心趋势
```

---

## 🛡️ 生产级稳定性

| 特性 | 实现方式 |
|------|---------|
| 跨平台路径兼容 | `CrossPlatformPathMiddleware` 自动纠错 Windows/Linux 路径差异 |
| 工具执行熔断 | `@timeout_fallback(timeout_seconds=15)` 装饰器，超时优雅降级 |
| 极速响应设计 | Lead Agent 提示词级别的任务并行优化，压制冗余计划轮次 |
| 后台异步复盘 | 任务完成后异步归档对话特征，不阻塞主流程 |
| 性能全链路监控 | `TimingMiddleware` 记录每次 LLM 调用和工具调用耗时，精确定位瓶颈 |

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **Agent 编排** | [deepagents](https://github.com/deepinsight/deepagents) · LangGraph |
| **LLM 模型** | 兼容 OpenAI API（GLM-4-Plus / GLM-4-Flash / GPT-4o 等） |
| **实时搜索** | Tavily AI — 接入真实互联网，搜索政策与研报 |
| **优化建模** | PyPSA — 线性规划求解经济调度与基础设施规划 |
| **领域知识** | Custom Skills（现货交易 SOP · 储能技术规范）|

---

## 🚀 快速开始

```bash
# 1. 复制环境变量配置
cp .env.example .env
# 填入 OPENAI_API_KEY, OPENAI_API_BASE, TAVILY_API_KEY

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行多 Agent 协作演示
python -m src.agents.demo.multi_agent_demo
```

---

## 🗺️ 领域扩展

新增一个专家 Agent 只需 4 步：

1. 在 `src/agents/domains/` 下新建领域目录（参考 `_template/`）
2. 继承 `DomainAgent`，声明工具与提示词
3. 在 `agent.py` 末尾调用 `AgentRegistry.register(YourAgent())`
4. 在 `domains/__init__.py` 的 `register_all_domains()` 中导入新包

系统会在下次启动时自动将新专家纳入 Lead Agent 的协作网络。

---

> *"通过 AI 赋能，让每一度电都创造最大的经济价值。"*
