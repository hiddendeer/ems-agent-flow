# LangChain 1.0+ 核心功能教程

> LangChain 是构建 LLM 应用的强大框架，本教程涵盖了最核心的 7 大功能模块，帮助您快速上手。

## 📋 目录

- [1. 文档基础设置](#1-文档基础设置)
  - [1.1 前言](#11-前言)
  - [1.2 环境配置和依赖安装](#12-环境配置和依赖安装)
- [2. LLM 集成](#2-llm-集成)
  - [2.1 LLM 集成基础](#21-llm-集成基础)
  - [2.2 模型选择和初始化](#22-模型选择和初始化)
  - [2.3 同步和异步调用](#23-同步和异步调用)
  - [2.4 常用参数配置](#24-常用参数配置)
- [3. 提示词模板](#3-提示词模板)
  - [3.1 提示词模板基础](#31-提示词模板基础)
  - [3.2 变量注入](#32-变量注入)
  - [3.3 部分模板](#33-部分模板)
- [4. 链式调用](#4-链式调用)
  - [4.1 链式调用基础](#41-链式调用基础)
  - [4.2 简单链](#42-简单链)
  - [4.3 顺序链](#43-顺序链)
  - [4.4 路由链](#44-路由链)
- [5. 记忆功能](#5-记忆功能)
  - [5.1 记忆功能概述](#51-记忆功能概述)
  - [5.2 会话记忆](#52-会话记忆)
  - [5.3 摘要记忆](#53-摘要记忆)
  - [5.4 向量存储记忆](#54-向量存储记忆)
- [6. 智能体](#6-智能体)
  - [6.1 智能体基础](#61-智能体基础)
  - [6.2 工具定义](#62-工具定义)
  - [6.3 智能体执行器](#63-智能体执行器)
- [7. 工具功能](#7-工具功能)
  - [7.1 工具概述](#71-工具概述)
  - [7.2 常用内置工具](#72-常用内置工具)
  - [7.3 自定义工具](#73-自定义工具)
  - [7.4 工具调用流程](#74-工具调用流程)
- [8. 检索功能](#8-检索功能)
  - [8.1 检索功能概述](#81-检索功能概述)
  - [8.2 文档加载器](#82-文档加载器)
  - [8.3 文本分块](#83-文本分块)
  - [8.4 向量嵌入](#84-向量嵌入)
  - [8.5 向量存储和检索](#85-向量存储和检索)

---

## 1. 文档基础设置

### 1.1 前言

欢迎使用 LangChain 1.0+ 核心功能教程！

本教程的目标：
- 🎯 帮助您快速掌握 LangChain 的核心概念
- 📚 提供可直接运行的代码示例
- 🔧 涵盖最常用的 7 大功能模块
- 💡 每个模块包含清晰的说明和注释

**本教程使用的 LangChain 版本：** 1.0+（最新稳定版）

> ⚠️ **注意**：LangChain 更新频繁，建议在实际使用前查看[官方最新文档](https://python.langchain.com/docs/introduction)。

---

### 1.2 环境配置和依赖安装

#### 安装 LangChain

使用 pip 安装最新版本的 LangChain：

```bash
pip install langchain
```

如果使用特定功能，可能需要额外安装以下包：

```bash
# OpenAI 集成
pip install langchain-openai

# 常用嵌入模型
pip install langchain-community

# 如果需要向量数据库
pip install chromadb  # 或其他向量数据库
```

#### 配置 API 密钥

本教程中的某些示例需要使用 LLM 的 API 密钥（如 OpenAI）。请按以下方式配置：

**方式一：使用环境变量（推荐）**

```bash
# Windows
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY=your-api-key-here
```

**方式二：在代码中直接设置（仅用于测试）**

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

> 🔐 **安全提示**：请勿将 API 密钥提交到代码仓库。使用环境变量或 .env 文件管理密钥。

---

## 2. LLM 集成

### 2.1 LLM 集成基础

LangChain 的核心是与各种大语言模型（LLM）进行交互。LLM 是 LangChain 应用的核心组件。

#### 支持的 LLM 提供商

LangChain 1.0+ 支持多种 LLM 提供商：

| 提供商 | LangChain 包 | 用途 |
|---------|--------------|------|
| OpenAI | `langchain-openai` | 通用任务、聊天 |
| Anthropic | `langchain-anthropic` | 长文本处理 |
| Google | `langchain-google-genai` | 集成 Google 服务 |
| Azure OpenAI | `langchain-openai` | 企业级 Azure 部署 |
| 本地模型 | `langchain-community` | Ollama、Hugging Face 等 |

---

### 2.2 模型选择和初始化

#### 使用 OpenAI 模型

```python
from langchain_openai import ChatOpenAI

# 初始化模型
llm = ChatOpenAI(
    model="gpt-4o",  # 或 gpt-3.5-turbo
    temperature=0.7,  # 控制输出随机性（0-2，越高越随机）
    max_tokens=1000,   # 最大输出 token 数
    api_key=os.getenv("OPENAI_API_KEY")  # 从环境变量读取
)
```

#### 调用 LLM 生成响应

**同步调用**

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

# 简单的文本生成
response = llm.invoke("你好，请用一句话介绍 LangChain。")
print(response.content)
# 输出：LangChain 是一个强大的框架，用于构建基于大语言模型的应用程序...
```

**带历史消息的对话**

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

llm = ChatOpenAI(model="gpt-4o")

messages = [
    SystemMessage(content="你是一个助手。"),
    HumanMessage(content="LangChain 是什么？"),
    AIMessage(content="LangChain 是..."),
    HumanMessage(content="它有什么用途？")
]

response = llm.invoke(messages)
print(response.content)
```

---

### 2.3 同步和异步调用

LangChain 1.0+ 原生支持异步操作，可以显著提高并发性能。

#### 异步 LLM 调用

```python
from langchain_openai import ChatOpenAI

# 初始化异步 LLM
llm = ChatOpenAI(model="gpt-4o")

# 异步调用
async def generate_async():
    response = await llm.ainvoke("用异步方式调用我")
    print(response.content)

# 运行异步函数
import asyncio
asyncio.run(generate_async())
```

#### 并发批量调用

```python
import asyncio
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

async def concurrent_calls():
    # 同时发起多个请求
    prompts = ["问题1", "问题2", "问题3"]
    responses = await asyncio.gather(*[llm.ainvoke(p) for p in prompts])
    for i, resp in enumerate(responses):
        print(f"响应 {i+1}: {resp.content}")

asyncio.run(concurrent_calls())
```

---

### 2.4 常用参数配置

| 参数 | 类型 | 说明 | 推荐值 |
|-----|------|------|---------|
| `temperature` | float | 输出随机性，0-2 | 0.7（创造性）或 0.0（确定性） |
| `max_tokens` | int | 最大输出 token 数 | 1000-4000 |
| `top_p` | float | 核采样概率，0-1 | 0.9 |
| `frequency_penalty` | float | 重复惩罚，-2.0 到 2.0 | 0.0 |
| `presence_penalty` | float | 存在惩罚，-2.0 到 2.0 | 0.0 |

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.3,      # 低温度，更确定性输出
    max_tokens=2000,      # 限制输出长度
    top_p=0.9,          # 高多样性
)
```

---

## 3. 提示词模板

### 3.1 提示词模板基础

提示词模板允许你标准化和重用提示，避免硬编码。

#### 基础模板使用

```python
from langchain_core.prompts import ChatPromptTemplate

# 创建模板
template = """
你是一个{name}。
请用{tone}的语气回答：{question}
"""

prompt = ChatPromptTemplate.from_template(template)

# 填充变量
formatted_prompt = prompt.format(
    name="Python 助手",
    tone="友好",
    question="什么是列表推导？"
)

print(formatted_prompt)
```

#### 输出到 LLM

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o")

# 创建提示模板
template = "用一句话解释：{topic}"
prompt = ChatPromptTemplate.from_template(template)

# 链接 LLM 和模板
chain = prompt | llm
response = chain.invoke({"topic": "装饰器"})
print(response.content)
```

---

### 3.2 变量注入

#### 使用 .format() 方法

```python
from langchain_core.prompts import ChatPromptTemplate

template = """
产品名称：{product}
价格：{price}
库存：{stock}
"""

prompt = ChatPromptTemplate.from_template(template)

# 填充多个变量
formatted = prompt.format(
    product="智能手机",
    price=3999,
    stock=100
)
```

#### 输入验证

LangChain 自动验证模板中的变量是否全部提供，缺失时会抛出错误。

```python
# 如果缺失变量
prompt.format(product="智能手机")  # 缺少 price 和 stock
# 抛出：KeyError: 'price'
```

---

### 3.3 部分模板

部分模板允许你预先固定一些变量，只留部分变量在运行时填充。

```python
from langchain_core.prompts import ChatPromptTemplate

# 创建部分模板（固定 product_name）
partial_template = """
产品：{product_name}
描述：{description}
价格：{price}
"""

partial_prompt = ChatPromptTemplate.from_template(partial_template)

# 固定 product_name，只留其他变量
fixed_prompt = partial_prompt.partial(product_name="笔记本")

# 只需要填充分部变量
formatted = fixed_prompt.format(
    description="高性能办公电脑",
    price=5999
)
print(formatted)
```

**使用场景**：当某些变量在所有提示中都相同时，使用部分模板可以避免重复设置。

---

## 4. 链式调用

### 4.1 链式调用基础

链（Chain）是将多个组件（LLM、工具、提示模板等）连接起来，形成处理流程。

**链的优势**：
- 🔄 流程清晰：将复杂任务分解为多个步骤
- 🧩 组合灵活：可自由组合 LLM、工具、记忆等组件
- ♻️ 可重用：链本身可以作为更大链的一部分

#### 最简单的链：提示 + LLM

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o")
template = "用中文解释：{word}"
prompt = ChatPromptTemplate.from_template(template)

# 使用管道符 | 连接提示和 LLM
chain = prompt | llm

# 调用链
response = chain.invoke({"word": "闭包"})
print(response.content)
```

---

### 4.2 简单链

简单链（SimpleChain）是最基础的链类型，只有一个 LLM 和一个提示。

```python
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate

llm = ChatOpenAI(model="gpt-4o")
template = "讲一个关于{topic}的笑话"
prompt = PromptTemplate(template=template)

# 创建简单链
chain = LLMChain(llm=llm, prompt=prompt)

# 执行
joke = chain.invoke({"topic": "编程"})
print(joke["text"])
```

---

### 4.3 顺序链

顺序链（SequentialChain）按顺序执行多个链，前一个链的输出是后一个链的输入。

```python
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, SimpleSequentialChain
from langchain_core.prompts import PromptTemplate

llm = ChatOpenAI(model="gpt-4o")

# 链 1：生成故事标题
title_prompt = PromptTemplate(template="为{theme}起一个吸引人的标题")
title_chain = LLMChain(llm=llm, prompt=title_prompt)

# 链 2：根据标题写故事
story_prompt = PromptTemplate(template="标题：{title}，主题：{theme}，写一个短故事")
story_chain = LLMChain(llm=llm, prompt=story_prompt)

# 组合为顺序链
overall_chain = SimpleSequentialChain(
    chains=[title_chain, story_chain],
    verbose=True
)

# 执行：前一个链的输出自动传递给后一个
result = overall_chain.invoke({"theme": "未来科技"})
print(f"标题：{result['title']}")
print(f"故事：{result['story']}")
```

---

### 4.4 路由链

路由链（Router Chain）根据输入类型选择不同的子链执行。

```python
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.chains.router import MultiPromptChain

llm = ChatOpenAI(model="gpt-4o")

# 定义多个提示模板
math_prompt = PromptTemplate(template="计算：{input}")
history_prompt = PromptTemplate(template="总结：{input}")
general_prompt = PromptTemplate(template="回答：{input}")

# 创建多个链
math_chain = LLMChain(llm=llm, prompt=math_prompt)
history_chain = LLMChain(llm=llm, prompt=history_prompt)
general_chain = LLMChain(llm=llm, prompt=general_prompt)

# 路由链：根据输入类型选择
router_chain = MultiPromptChain(
    router_llm=llm,
    default_chain=general_chain,
    destination_chains={
        "数学": math_chain,
        "历史": history_chain
    },
    destination_inputs={
        "数学": ["input"],
        "历史": ["input"]
    }
)

# 执行
result = router_chain.invoke({
    "input": "2 + 2 = ?",
    "text": "Python 的历史"
})
print(result["text"])
```

---

## 5. 记忆功能

### 5.1 记忆功能概述

记忆（Memory）允许 LLM 在对话中记住之前的信息，实现有状态的对话。

**记忆类型**：
- 📝 会话记忆：保存完整的对话历史
- 📄 摘要记忆：对历史进行总结，节省 token
- 🗄️ 向量存储记忆：基于向量检索相关历史

---

### 5.2 会话记忆

#### ConversationBufferMemory

保存最近的对话历史，适合短对话。

```python
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

llm = ChatOpenAI(model="gpt-4o")

# 创建缓冲记忆
memory = ConversationBufferMemory(
    memory_key="chat_history",  # 存储键
    return_messages=True  # 返回消息对象
)

# 创建带记忆的对话链
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# 第一轮对话
response1 = conversation.invoke({"input": "我叫张三"})
print(f"回复 1：{response1['response']}")

# 第二轮对话：LLM 记住了名字
response2 = conversation.invoke({"input": "我叫什么名字？"})
print(f"回复 2：{response2['response']}")  # 应该回答：张三
```

---

### 5.3 摘要记忆

#### ConversationSummaryMemory

对长对话进行总结，避免超出 token 限制。

```python
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from langchain.chains import ConversationChain

llm = ChatOpenAI(model="gpt-4o")

# 创建摘要记忆（需要一个用于摘要的 LLM）
summary_memory = ConversationSummaryMemory(
    llm=llm,
    max_token_limit=500,  # 超过限制时进行摘要
    return_messages=True
)

conversation = ConversationChain(
    llm=llm,
    memory=summary_memory,
    verbose=True
)

# 长对话会自动总结
for msg in ["你好", "介绍一下 LangChain", "它有什么优势？", "总结一下"]:
    response = conversation.invoke({"input": msg})
    print(f"回复：{response['response']}")
```

---

### 5.4 向量存储记忆

#### VectorStoreRetrieverMemory

基于向量数据库存储和检索对话历史。

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain

llm = ChatOpenAI(model="gpt-4o")
embeddings = OpenAIEmbeddings()

# 创建向量存储
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings
)

# 创建向量检索记忆
memory = VectorStoreRetrieverMemory(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),  # 检索最近的 2 条
    memory_key="chat_history"
)

conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True
)

# 对话历史会被向量化存储，后续可以检索
response = conversation.invoke({"input": "我们之前聊了什么？"})
print(response["response"])
```

---

## 6. 智能体

### 6.1 智能体基础

智能体（Agent）是能够自主思考和调用工具的 LLM 系统。

**智能体的工作流程**：
1. 🤔 接收任务
2. 🧠 思考：需要什么工具，如何调用
3. 🔧 调用工具：执行工具获取结果
4. 📝 形成最终答案

---

### 6.2 工具定义

#### 内置工具

LangChain 提供多种内置工具，如搜索、计算、Python REPL。

```python
from langchain_community.tools import TavilySearchResults  # 搜索工具
from langchain_community.tools import ShellTool  # 执行 shell 命令

# 直接使用工具
search_tool = TavilySearchResults(
    max_results=5,
    search_depth="basic"
)

# 执行工具
results = search_tool.run("最新 LangChain 版本")
print(results)
```

#### 自定义工具

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from typing import Type

class CalculatorInput(BaseModel):
    """计算器输入"""
    a: float = Field(description="第一个数字")
    b: float = Field(description="第二个数字")
    operation: str = Field(description="操作：add, subtract, multiply, divide")

class Calculator(StructuredTool):
    """简单的计算器工具"""
    name = "calculator"
    description = "执行基本数学运算"
    args_schema: Type[CalculatorInput] = CalculatorInput

    def _run(self, a: float, b: float, operation: str):
        """执行计算"""
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b != 0:
                return a / b
            return "除数不能为零"

# 创建工具实例
calculator_tool = Calculator()
```

---

### 6.3 智能体执行器

#### 创建 ReAct 智能体

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool

llm = ChatOpenAI(model="gpt-4o")

# 使用之前的计算器工具
tools = [calculator_tool]

# 创建 ReAct 智能体
agent = create_react_agent(
    llm=llm,
    tools=tools,
    verbose=True,  # 显示思考过程
    handle_parsing_errors=True  # 处理解析错误
)

# 创建执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,  # 最大思考迭代次数
)

# 执行智能体
result = agent_executor.invoke({"input": "计算 25 乘以 4"})
print(result["output"])  # 应该输出：100
```

#### 智能体对话

```python
# 创建带历史记录的智能体
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferMemory

llm = ChatOpenAI(model="gpt-4o")

memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

agent = create_react_agent(
    llm=llm,
    tools=[calculator_tool],
    verbose=True
)

executor = AgentExecutor(
    agent=agent,
    tools=[calculator_tool],
    memory=memory,  # 添加记忆
    verbose=True
)

# 智能体会记住之前的对话
response1 = executor.invoke({"input": "记住：今天天气晴朗"})
response2 = executor.invoke({"input": "今天天气怎么样？"})
print(response2["output"])  # 应该引用之前的记忆
```

---

## 7. 工具功能

### 7.1 工具概述

工具（Tool）是智能体可以调用的函数，扩展 LLM 的能力。

**工具类型**：
- 🔍 搜索工具：联网搜索信息
- 🧮 计算工具：执行数学运算
- 💻️ Python 工具：执行 Python 代码
- 🌐 API 工具：调用外部 API

---

### 7.2 常用内置工具

#### 搜索工具

```python
from langchain_community.tools import TavilySearchResults

# 配置搜索工具
search = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_domains=["python.org", "langchain.com"]  # 限制搜索域
)

# 使用
results = search.run("Python 最新的特性")
for result in results:
    print(f"标题：{result['title']}")
    print(f"链接：{result['link']}")
```

#### Python REPL 工具

```python
from langchain_community.tools import PythonREPLTool

# Python REPL 允许智能体执行 Python 代码
python_repl = PythonREPLTool()

# 使用
result = python_repl.run("print([x**2 for x in range(5)])")
print(result)  # 输出：[0, 1, 4, 9, 16]
```

---

### 7.3 自定义工具

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

# 定义输入模型
class WeatherInput(BaseModel):
    """天气查询输入"""
    city: str = Field(description="城市名称")

# 定义天气工具
class WeatherTool(StructuredTool):
    """查询天气的工具（模拟）"""
    name = "get_weather"
    description = "查询指定城市的天气"
    args_schema: Type[WeatherInput] = WeatherInput

    def _run(self, city: str):
        """返回模拟天气数据"""
        weather_data = {
            "北京": "晴，25°C",
            "上海": "多云，28°C",
            "深圳": "小雨，22°C"
        }
        return weather_data.get(city, "未知城市")

# 创建工具实例
weather_tool = WeatherTool()

# 在智能体中使用
from langchain.agents import create_react_agent, AgentExecutor

llm = ChatOpenAI(model="gpt-4o")
agent = create_react_agent(llm, tools=[weather_tool])
executor = AgentExecutor(agent=agent, tools=[weather_tool])

# 智能体会自动调用工具
result = executor.invoke({"input": "北京天气怎么样？"})
print(result["output"])  # 输出：晴，25°C
```

---

### 7.4 工具调用流程

#### 绑定工具到 LLM

```python
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# 使用装饰器定义工具
@tool
def get_current_time():
    """获取当前时间"""
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

llm = ChatOpenAI(model="gpt-4o")

# 将工具绑定到 LLM
llm_with_tools = llm.bind_tools([get_current_time])

# LLM 可以自动决定是否调用工具
response = llm_with_tools.invoke("现在几点了？")
print(response.content)
```

#### 理解析工具调用

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools([get_current_time])

# 设置为并行调用模式
llm_with_tools_parallel = llm.bind_tools([get_current_time], parallel_tool_calls=True)

response = llm_with_tools_parallel.invoke("查询北京、上海、深圳的时间")
# 如果 LLM 判断可以并行调用，会同时发起多个工具调用
print(response.tool_calls)  # 查看调用的工具
```

---

## 8. 检索功能

### 8.1 检索功能概述

检索增强生成（RAG）结合了向量搜索和 LLM 生成，让 LLM 基于特定文档回答问题。

**RAG 流程**：
1. 📄 加载文档
2. ✂️ 分割文本
3. 🔢 转换为向量
4. 💾 存储向量
5. 🔍 检索相关内容
6. 💬 生成回答

---

### 8.2 文档加载器

#### TextLoader（文本文件）

```python
from langchain_community.document_loaders import TextLoader

# 加载文本文件
loader = TextLoader("example.txt")
documents = loader.load()

print(f"加载了 {len(documents)} 个文档")
print(f"第一个文档内容：{documents[0].page_content[:100]}...")
```

#### PyPDFLoader（PDF 文件）

```python
from langchain_community.document_loaders import PyPDFLoader

# 加载 PDF
loader = PyPDFLoader("manual.pdf", extract_images=False)
documents = loader.load()

print(f"PDF 页数：{len(documents)}")
```

#### 多种加载器

| 加载器 | 文件类型 | 用途 |
|--------|----------|------|
| `TextLoader` | .txt, .md | 纯文本 |
| `PyPDFLoader` | .pdf | PDF 文档 |
| `UnstructuredPDFLoader` | .pdf | 带格式的 PDF |
| `WebBaseLoader` | URL | 网页内容 |
| `CSVLoader` | .csv | CSV 数据 |

---

### 8.3 文本分块

#### CharacterTextSplitter

```python
from langchain_text_splitters import CharacterTextSplitter

# 创建分割器
splitter = CharacterTextSplitter(
    separator="\n\n",    # 按段落分割
    chunk_size=1000,     # 每块最大字符数
    chunk_overlap=200,   # 块之间重叠字符数
    length_function=len,
)

# 分割文档
texts = splitter.split_text(documents[0].page_content)

print(f"分割为 {len(texts)} 个块")
print(f"第一个块：{texts[0][:50]}...")
```

#### RecursiveCharacterTextSplitter（推荐）

递归分割器会尝试保持语义完整性。

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 递归分割器（更智能）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", "。", "，", "、"]  # 按中文标点分割
)

texts = splitter.split_text(large_text)
```

---

### 8.4 向量嵌入

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 创建嵌入模型（将文本转为向量）
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # 或 text-embedding-3-large
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# 生成文本的向量
text = "LangChain 是一个强大的框架"
vector = embeddings.embed_query(text)

print(f"向量维度：{len(vector)}")
print(f"前 5 个值：{vector[:5]}")
```

#### 批量嵌入（更高效）

```python
texts = ["文本1", "文本2", "文本3"]

# 批量生成向量
vectors = embeddings.embed_documents(texts)

print(f"生成了 {len(vectors)} 个向量")
```

---

### 8.5 向量存储和检索

#### Chroma 向量数据库

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 创建向量存储
vectorstore = Chroma(
    collection_name="my_documents",  # 集合名称
    embedding_function=OpenAIEmbeddings(),
    persist_directory="./chroma_db",  # 持久化目录
)

# 添加文档到向量库
vectorstore.add_documents(documents=split_texts)

# 创建检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",  # 相似度搜索
    search_kwargs={"k": 3}        # 返回最相关的 3 个结果
)

# 检索相关文档
results = retriever.invoke("什么是 LangChain？")
for doc in results:
    print(f"相关内容：{doc.page_content}")
```

#### 完整的 RAG 流程

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import create_retrieval_chain
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. 加载文档
loader = TextLoader("knowledge_base.txt")
docs = loader.load()

# 2. 分割文本
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = splitter.split_documents(docs)

# 3. 创建向量存储
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# 4. 创建检索器
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 5. 创建 RAG 链
llm = ChatOpenAI(model="gpt-4o")
retrieval_chain = create_retrieval_chain(
    llm=llm,
    retriever=retriever,
    return_source_documents=True  # 返回引用的文档
)

# 6. 提问并检索相关文档回答
response = retrieval_chain.invoke({"query": "LangChain 如何使用记忆功能？"})

print(f"回答：{response['answer']}")
print(f"引用的文档：")
for doc in response["source_documents"]:
    print(f"  - {doc.metadata.get('source', '未知')}")
```

---

## 🎯 总结

本教程涵盖了 LangChain 1.0+ 的 7 大核心功能：

1. ✅ **LLM 集成**：模型选择、同步/异步调用、参数配置
2. ✅ **提示词模板**：模板创建、变量注入、部分模板
3. ✅ **链式调用**：简单链、顺序链、路由链
4. ✅ **记忆功能**：会话记忆、摘要记忆、向量存储
5. ✅ **智能体**：工具定义、执行器、ReAct 模式
6. ✅ **工具功能**：内置工具、自定义工具、工具调用
7. ✅ **检索功能**：文档加载、文本分块、向量嵌入、检索

---

## 📚 下一步学习

- 查看 [LangChain 官方文档](https://python.langchain.com/docs/introduction)
- 学习 [LangGraph](https://langchain-ai.github.io/langgraph/)（高级工作流）
- 探索 [LangSmith](https://www.langchain.com/langsmith)（调试和监控）

---

**祝你学习愉快！如有问题，欢迎查阅官方文档或社区资源。**
