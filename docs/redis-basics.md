# Redis 基础知识文档

> **适用范围**: 本文档面向 FastAPI 后端开发者,提供 Redis 核心概念、数据类型和最佳实践指南。
>
> **Redis 版本**: 基于 Redis 6.0+
>
> **官方文档**: [Redis 官方文档](https://redis.io/documentation)

## 目录

1. [Redis 核心概念](#1-redis-核心概念)
2. [Redis 数据类型详解](#2-redis-数据类型详解)
3. [Python/FastAPI 集成](#3-pythonfastapi-集成)
4. [Redis 常见用法和最佳实践](#4-redis-常见用法和最佳实践)
5. [性能优化](#5-性能优化)
6. [安全配置](#6-安全配置)
7. [监控和运维](#7-监控和运维)

---

## 1. Redis 核心概念

### 1.1 什么是 Redis

Redis (Remote Dictionary Server) 是一个开源的内存键值数据库,具有以下特点:

- **内存存储**: 数据主要存储在内存中,读写速度极快
- **键值存储**: 使用 Key-Value 模型存储数据
- **数据持久化**: 支持 RDB 和 AOF 两种持久化方式
- **丰富的数据类型**: 支持多种数据结构(String、Hash、List、Set、Sorted Set 等)
- **单线程模型**: 主要工作线程是单线程,避免上下文切换开销

### 1.2 Redis 常见应用场景

✅ **缓存**: 数据库查询缓存、API 响应缓存
✅ **会话存储**: 用户登录状态、会话数据
✅ **消息队列**: 异步任务处理、事件驱动
✅ **排行榜**: 游戏排名、评分系统
✅ **计数器**: 访问统计、点赞数、库存管理
✅ **分布式锁**: 防止并发冲突
✅ **标签系统**: 用户标签、内容分类
✅ **最新列表**: 最新动态、消息列表

### 1.3 Redis 基本架构

**单机模式**:
- 最简单的部署方式
- 适合开发测试和小规模应用

**哨兵模式 (Sentinel)**:
- 高可用方案
- 自动故障转移
- 主从复制 + 哨兵监控

**集群模式 (Cluster)**:
- 水平扩展
- 数据分片
- 适合大规模应用

### 1.4 安装和快速启动

#### Docker 方式 (推荐)

```bash
# 拉取 Redis 镜像
docker pull redis:7

# 启动 Redis 容器
docker run -d -p 6379:6379 --name myredis redis:7

# 连接测试
docker exec -it myredis redis-cli
```

#### 配置文件方式

```bash
# 启动 Redis
redis-server /path/to/redis.conf

# 使用命令行客户端
redis-cli
```

---

## 2. Redis 数据类型详解

### 2.1 String (字符串)

**用途**: 存储文本、数字、二进制数据

**常用命令**:

```bash
SET key value           # 设置值
GET key                 # 获取值
SETEX key seconds value # 设置值并指定过期时间
INCR key                # 自增 1
DECR key                # 自减 1
INCRBY key increment    # 指定增量自增
MGET key1 key2          # 批量获取
MSET key1 val1 key2 val2 # 批量设置
```

**Python 示例**:

```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 基本操作
r.set('user:1001:name', '张三')
name = r.get('user:1001:name')
print(name)  # 输出: 张三

# 计数器
r.incr('article:1001:views')
views = r.get('article:1001:views')
print(f'阅读量: {views}')

# 带过期时间的缓存
r.setex('cache:user:1001', 3600, 'cached_data')  # 1小时过期

# 批量操作
values = r.mget('user:1001:name', 'article:1001:views')
```

**应用场景**:
- ✅ 页面浏览计数
- ✅ 分布式 ID 生成
- ✅ 会话 Token 存储
- ✅ 缓存热点数据

---

### 2.2 Hash (哈希)

**用途**: 存储对象,适合存储结构化数据

**常用命令**:

```bash
HSET key field value     # 设置字段值
HGET key field           # 获取字段值
HMGET key field1 field2  # 批量获取字段
HGETALL key              # 获取所有字段和值
HDEL key field           # 删除字段
HEXISTS key field        # 判断字段是否存在
HINCRBY key field incr   # 字段值自增
```

**Python 示例**:

```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 存储用户信息
r.hset('user:1001', mapping={
    'name': '张三',
    'age': '28',
    'email': 'zhangsan@example.com'
})

# 获取单个字段
name = r.hget('user:1001', 'name')
print(name)  # 输出: 张三

# 获取多个字段
user_info = r.hmget('user:1001', ['name', 'email'])
print(user_info)  # 输出: ['张三', 'zhangsan@example.com']

# 获取所有字段
all_info = r.hgetall('user:1001')
print(all_info)  # 输出: {'name': '张三', 'age': '28', 'email': 'zhangsan@example.com'}

# 购物车示例
r.hset('cart:user:1001', 'product:2001', '2')  # 商品ID: 数量
r.hincrby('cart:user:1001', 'product:2001', 1)  # 数量+1
cart_items = r.hgetall('cart:user:1001')
```

**应用场景**:
- ✅ 用户信息存储
- ✅ 购物车管理
- ✅ 商品属性存储
- ✅ 配置管理

⚠️ **注意**: Hash 适合存储字段数量适中的对象(建议 < 1000 字段)

---

### 2.3 List (列表)

**用途**: 存储有序的字符串列表,支持两端插入/弹出

**常用命令**:

```bash
LPUSH key value1 value2  # 左侧插入
RPUSH key value1 value2  # 右侧插入
LPOP key                 # 左侧弹出
RPOP key                 # 右侧弹出
LRANGE key start stop    # 获取范围内元素
LLEN key                 # 获取列表长度
LTRIM key start stop     # 保留范围内元素
BLPOP key timeout        # 阻塞式左弹出
BRPOP key timeout        # 阻塞式右弹出
```

**Python 示例**:

```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 消息队列示例
r.lpush('queue:tasks', 'task1', 'task2', 'task3')

# 处理任务
task = r.rpop('queue:tasks')
print(f'处理任务: {task}')

# 获取队列长度
queue_length = r.llen('queue:tasks')
print(f'待处理任务数: {queue_length}')

# 最新动态列表
r.lpush('feed:user:1001', '发布了新文章', '点赞了评论')
recent_feeds = r.lrange('feed:user:1001', 0, 9)  # 获取最新10条
print(recent_feeds)

# 限制列表长度(保留最新100条)
r.lpush('log:errors', 'error_msg_1')
r.ltrim('log:errors', 0, 99)  # 保留前100条
```

**应用场景**:
- ✅ 消息队列
- ✅ 最新动态列表
- ✅ 日志收集
- ✅ 用户时间线

🚫 **警告**: List 索引时间复杂度为 O(N),大列表性能较差,建议控制长度

---

### 2.4 Set (集合)

**用途**: 存储无序的唯一元素集合,支持集合运算

**常用命令**:

```bash
SADD key member1 member2    # 添加成员
SMEMBERS key                # 获取所有成员
SISMEMBER key member        # 判断成员是否存在
SCARD key                   # 获取成员数量
SREM key member             # 删除成员
SPOP key count              # 随机弹出成员
SRANDMEMBER key count       # 随机获取成员(不删除)
SINTER key1 key2            # 交集
SUNION key1 key2            # 并集
SDIFF key1 key2             # 差集
```

**Python 示例**:

```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 标签系统
r.sadd('user:1001:tags', 'python', 'fastapi', 'redis')
r.sadd('user:1002:tags', 'python', 'django', 'mysql')

# 检查标签
has_tag = r.sismember('user:1001:tags', 'python')
print(f'用户有 python 标签: {has_tag}')

# 共同标签(交集)
common_tags = r.sinter('user:1001:tags', 'user:1002:tags')
print(f'共同标签: {common_tags}')  # 输出: {'python'}

# 所有标签(并集)
all_tags = r.sunion('user:1001:tags', 'user:1002:tags')
print(f'所有标签: {all_tags}')

# 抽奖系统
r.sadd('lottery:participants', 'user1', 'user2', 'user3', 'user4', 'user5')
winner = r.spop('lottery:participants')  # 随机抽取并移除
print(f'中奖用户: {winner}')

# 点赞用户去重
r.sadd('article:1001:likers', 'user:1001', 'user:1002')
already_liked = r.sismember('article:1001:likers', 'user:1001')
print(f'是否已点赞: {already_liked}')
```

**应用场景**:
- ✅ 标签系统
- ✅ 共同好友/关注
- ✅ 抽奖系统
- ✅ 点赞用户去重
- ✅ 数据去重

💡 **提示**: Set 自动去重,适合需要唯一性的场景

---

### 2.5 Sorted Set (有序集合)

**用途**: 存储有序的唯一元素,每个元素关联一个分数(score)

**常用命令**:

```bash
ZADD key score member      # 添加成员(可更新分数)
ZRANGE key start stop      # 按分数升序获取
ZREVRANGE key start stop   # 按分数降序获取
ZRANK key member           # 获取成员排名(升序)
ZREVRANK key member        # 获取成员排名(降序)
ZSCORE key member          # 获取成员分数
ZINCRBY key incr member    # 成员分数增加
ZCARD key                  # 获取成员数量
ZREM key member            # 删除成员
ZRANGEBYSCORE key min max  # 按分数范围获取
ZCOUNT key min max         # 统计分数范围内成员数
```

**Python 示例**:

```python
import redis
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 排行榜示例
r.zadd('leaderboard:game', {
    'player1': 1000,
    'player2': 1500,
    'player3': 1200,
    'player4': 1800
})

# 获取前10名(降序)
top10 = r.zrevrange('leaderboard:game', 0, 9, withscores=True)
print('Top 10:')
for rank, (player, score) in enumerate(top10, 1):
    print(f'{rank}. {player}: {score}')

# 获取玩家排名
player_rank = r.zrevrank('leaderboard:game', 'player2')
print(f'player2 排名: {player_rank + 1}')  # 排名从0开始,加1

# 更新分数
r.zincrby('leaderboard:game', 100, 'player1')

# 按分数范围查询
high_players = r.zrangebyscore('leaderboard:game', 1500, '+inf')
print(f'高分玩家: {high_players}')

# 延时队列
timestamp = int(time.time()) + 60  # 60秒后执行
r.zadd('delayed:queue', {f'task:{timestamp}': timestamp})

# 获取到期的任务
ready_tasks = zrangebyscore('delayed:queue', 0, int(time.time()))
```

**应用场景**:
- ✅ 游戏排行榜
- ✅ 评分系统
- ✅ 延时任务队列
- ✅ 范围查询(如按时间排序)

✅ **最佳实践**: 排行榜使用 ZREVRANGE 获取前N名,时间复杂度 O(log(N) + M)

---

## 3. Python/FastAPI 集成

### 3.1 Redis 连接配置

#### 安装依赖

```bash
pip install redis>=4.0.0
```

#### 基本连接

```python
import redis

# 单机连接
r = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    password=None,  # 如果有密码
    decode_responses=True,  # 自动解码为字符串
    socket_timeout=5,  # 超时时间(秒)
    socket_connect_timeout=5,
    retry_on_timeout=True
)

# 使用连接池(推荐)
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    max_connections=50  # 最大连接数
)
r = redis.Redis(connection_pool=pool)

# 测试连接
try:
    r.ping()
    print('Redis 连接成功')
except redis.ConnectionError as e:
    print(f'连接失败: {e}')
```

#### 哨兵模式连接

```python
from redis.sentinel import Sentinel

sentinel = Sentinel([
    ('sentinel1', 26379),
    ('sentinel2', 26379),
    ('sentinel3', 26379)
], socket_timeout=5)

# 获取主节点写入
master = sentinel.master_for('mymaster', socket_timeout=5)

# 获取从节点读取
slave = sentinel.slave_for('mymaster', socket_timeout=5)

master.set('key', 'value')
value = slave.get('key')
```

#### 环境变量配置

```python
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_DB = int(os.getenv('REDIS_DB', 0))

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True
)
```

⚠️ **注意**: 生产环境必须使用连接池,避免频繁创建连接

---

### 3.2 FastAPI 集成

#### 依赖注入方式

```python
from fastapi import FastAPI, Depends
import redis
from typing import Optional

app = FastAPI()

# 创建连接池
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

# 依赖注入函数
def get_redis():
    redis_client = redis.Redis(connection_pool=redis_pool)
    try:
        yield redis_client
    finally:
        # 不需要关闭,连接池会自动管理
        pass

# 使用示例
@app.get('/cache/{key}')
async def get_cache(key: str, r: redis.Redis = Depends(get_redis)):
    value = r.get(key)
    if value:
        return {'key': key, 'value': value}
    return {'error': 'Key not found'}, 404

@app.post('/cache/{key}')
async def set_cache(key: str, value: str, r: redis.Redis = Depends(get_redis)):
    r.set(key, value, ex=3600)  # 1小时过期
    return {'status': 'ok', 'key': key, 'value': value}
```

#### 缓存装饰器

```python
from functools import wraps
import json
import hashlib

def cache_result(expire: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            key_data = f'{func.__name__}:{args}:{kwargs}'
            cache_key = f'cache:{hashlib.md5(key_data.encode()).hexdigest()}'

            # 尝试从缓存获取
            r = redis.Redis(connection_pool=redis_pool)
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            r.setex(cache_key, expire, json.dumps(result, ensure_ascii=False))
            return result
        return wrapper
    return decorator

# 使用示例
@app.get('/expensive-operation')
@cache_result(expire=1800)  # 缓存30分钟
async def expensive_operation():
    # 模拟耗时操作
    import time
    time.sleep(2)
    return {'result': 'computed data', 'timestamp': time.time()}
```

#### 会话管理

```python
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

class SessionData(BaseModel):
    user_id: int
    username: str

def create_session(r: redis.Redis, user_id: int, username: str) -> str:
    """创建会话"""
    session_id = hashlib.md5(f'{user_id}:{time.time()}'.encode()).hexdigest()
    session_data = SessionData(user_id=user_id, username=username)

    r.setex(
        f'session:{session_id}',
        86400,  # 24小时
        json.dumps(session_data.dict())
    )
    return session_id

def get_session(r: redis.Redis, session_id: str) -> Optional[SessionData]:
    """获取会话"""
    data = r.get(f'session:{session_id}')
    if not data:
        return None
    return SessionData(**json.loads(data))

# 路由示例
@app.post('/login')
async def login(username: str, password: str, r: redis.Redis = Depends(get_redis)):
    # 验证用户名密码(省略)
    user_id = 1001  # 假设验证通过

    session_id = create_session(r, user_id, username)
    return {'session_id': session_id}

@app.get('/profile')
async def get_profile(session_id: str, r: redis.Redis = Depends(get_redis)):
    session = get_session(r, session_id)
    if not session:
        raise HTTPException(status_code=401, detail='Invalid session')

    return {'user_id': session.user_id, 'username': session.username}
```

#### 分布式锁

```python
import uuid

class DistributedLock:
    """分布式锁"""
    def __init__(self, redis_client: redis.Redis, key: str, expire: int = 10):
        self.r = redis_client
        self.key = f'lock:{key}'
        self.expire = expire
        self.identifier = str(uuid.uuid4())

    def acquire(self) -> bool:
        """获取锁"""
        return self.r.set(
            self.key,
            self.identifier,
            nx=True,  # 仅当键不存在时设置
            ex=self.expire  # 过期时间(秒)
        )

    def release(self) -> bool:
        """释放锁"""
        # 使用 Lua 脚本确保原子性
        lua_script = '''
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        '''
        result = self.r.eval(lua_script, 1, self.key, self.identifier)
        return bool(result)

# 使用示例
@app.post('/deduct-inventory/{product_id}')
async def deduct_inventory(product_id: int, r: redis.Redis = Depends(get_redis)):
    lock = DistributedLock(r, f'inventory:{product_id}', expire=5)

    if not lock.acquire():
        raise HTTPException(status_code=429, detail='操作频繁,请稍后重试')

    try:
        # 执行业务逻辑
        current = int(r.get(f'inventory:{product_id}') or 0)
        if current > 0:
            r.decr(f'inventory:{product_id}')
            return {'remaining': current - 1}
        else:
            raise HTTPException(status_code=400, detail='库存不足')
    finally:
        lock.release()
```

---

## 4. Redis 常见用法和最佳实践

### 4.1 缓存策略

#### Cache-Aside 模式(推荐)

```python
# 读取流程
def get_user(user_id: int):
    r = redis.Redis(connection_pool=redis_pool)

    # 1. 先查缓存
    cached = r.get(f'user:{user_id}')
    if cached:
        return json.loads(cached)

    # 2. 缓存未命中,查询数据库
    user = db.query(User).filter(User.id == user_id).first()

    # 3. 写入缓存
    if user:
        r.setex(f'user:{user_id}', 3600, json.dumps(user.to_dict()))

    return user

# 更新流程
def update_user(user_id: int, data: dict):
    r = redis.Redis(connection_pool=redis_pool)

    # 1. 更新数据库
    db.query(User).filter(User.id == user_id).update(data)
    db.commit()

    # 2. 删除缓存
    r.delete(f'user:{user_id}')
```

#### Write-Through 模式

```python
# 写入时同时更新缓存和数据库
def set_user(user_id: int, data: dict):
    r = redis.Redis(connection_pool=redis_pool)

    # 同时写入缓存和数据库
    r.setex(f'user:{user_id}', 3600, json.dumps(data))
    db.query(User).filter(User.id == user_id).update(data)
    db.commit()
```

#### Write-Behind 模式

```python
# 异步批量写入,适合高并发写入场景
# 简化示例,实际需要更复杂的队列和批处理逻辑
```

#### 缓存过期策略

```python
# 设置固定过期时间
r.setex('key', 3600, 'value')  # 1小时后过期

# 设置过期时间
r.expire('key', 3600)

# 查看剩余时间
ttl = r.ttl('key')  # 返回秒数,-1表示永不过期,-2表示键不存在

# 随机过期时间,防止缓存雪崩
import random
expire_time = 3600 + random.randint(0, 300)  # 1小时+0-5分钟随机
r.setex('key', expire_time, 'value')
```

#### 缓存穿透解决方案

```python
def get_data_with_protection(key: str):
    r = redis.Redis(connection_pool=redis_pool)

    # 1. 查询缓存
    cached = r.get(f'data:{key}')
    if cached == 'NULL':  # 缓存空值
        return None
    if cached:
        return json.loads(cached)

    # 2. 查询数据库
    data = db.query(Data).filter(Data.key == key).first()

    # 3. 缓存结果
    if data:
        r.setex(f'data:{key}', 3600, json.dumps(data.to_dict()))
    else:
        # 缓存空值,防止穿透
        r.setex(f'data:{key}', 300, 'NULL')  # 短时间缓存

    return data
```

#### 缓存击穿解决方案

```python
# 使用互斥锁
def get_hot_data(key: str):
    r = redis.Redis(connection_pool=redis_pool)

    # 检查缓存
    cached = r.get(key)
    if cached:
        return json.loads(cached)

    # 获取锁
    lock_key = f'lock:{key}'
    lock_acquired = r.set(lock_key, '1', nx=True, ex=10)

    if lock_acquired:
        try:
            # 双重检查
            cached = r.get(key)
            if cached:
                return json.loads(cached)

            # 查询数据库
            data = db.query(HotData).filter(HotData.key == key).first()

            # 更新缓存
            if data:
                r.setex(key, 3600, json.dumps(data.to_dict()))
            return data
        finally:
            r.delete(lock_key)
    else:
        # 未获取到锁,短暂等待后重试
        time.sleep(0.1)
        return get_hot_data(key)
```

#### 缓存雪崩解决方案

```python
# 1. 随机过期时间(见上文)
# 2. 使用 Redis 持久化,重启后自动加载缓存
# 3. 多级缓存(本地缓存 + Redis)
# 4. 限流降级
```

---

### 4.2 性能优化

#### 批量操作

```python
# 使用 MGET 代替多次 GET
# 慢速方式
values = [r.get(f'key:{i}') for i in range(100)]  # 100次网络往返

# 快速方式
keys = [f'key:{i}' for i in range(100)]
values = r.mget(keys)  # 1次网络往返

# 使用 MSET 代替多次 SET
data = {f'key:{i}': f'value:{i}' for i in range(100)}
r.mset(data)

# Pipeline 批量执行
pipe = r.pipeline()
for i in range(100):
    pipe.set(f'key:{i}', f'value:{i}')
pipe.execute()
```

#### Pipeline 技术

```python
# Pipeline 减少网络往返
pipe = r.pipeline()

# 添加多个命令
pipe.set('key1', 'value1')
pipe.get('key1')
pipe.incr('counter')

# 一次性执行
results = pipe.execute()
print(results)  # [True, 'value1', 1]
```

#### 内存优化

```python
# 1. 使用合适的数据结构
# Hash 适合对象,String 适合简单值

# 2. 设置过期时间,清理无用数据
r.setex('temp_key', 300, 'value')

# 3. 使用压缩(对于大对象)
import gzip
import pickle

data = {'large': 'data' * 10000}
compressed = gzip.compress(pickle.dumps(data))
r.set('key', compressed)

# 解压
raw = r.get('key')
decompressed = pickle.loads(gzip.decompress(raw))
```

#### 慢查询分析

```bash
# 配置慢查询日志(单位:微秒)
CONFIG SET slowlog-log-slower-than 10000  # 超过10ms记录
CONFIG SET slowlog-max-len 128  # 最多保留128条

# 查看慢查询
SLOWLOG GET 10  # 获取最近10条
SLOWLOG LEN     # 慢查询数量
SLOWLOG RESET   # 清空慢查询日志
```

---

## 5. 性能优化

### 5.1 批量操作优化

```python
# 使用 Pipeline 批量执行
pipe = r.pipeline(transaction=False)  # 禁用事务以提高性能
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
pipe.execute()

# 使用 Lua 脚本减少网络往返
lua_script = '''
for i = 1, 1000 do
    redis.call("SET", "key:" .. i, "value:" .. i)
end
'''
r.eval(lua_script, 0)
```

### 5.2 内存优化建议

✅ 使用 Hash 代替多个 String 键
✅ 设置合理的过期时间
✅ 使用数据结构编码优化(ziplist、intset)
✅ 定期清理无用数据
✅ 监控内存使用率,设置 maxmemory

### 5.3 连接池配置

```python
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,  # 根据并发量调整
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30  # 健康检查
)
```

---

## 6. 安全配置

### 6.1 密码认证

```bash
# redis.conf
requirepass your_strong_password

# 连接时指定密码
r = redis.Redis(
    host='localhost',
    port=6379,
    password='your_strong_password'
)
```

### 6.2 网络隔离

🚫 **警告**: 不要将 Redis 暴露在公网

```bash
# redis.conf
bind 127.0.0.1  # 仅本地访问
# 或使用防火墙限制访问
```

### 6.3 禁用危险命令

```bash
# redis.conf
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
rename-command SHUTDOWN ""
```

### 6.4 ACL 权限控制(Redis 6.0+)

```bash
# 创建用户
ACL SETUSER user1 on >password ~user:* +@read

# 使用
r = redis.Redis(username='user1', password='password')
```

### 6.5 安全检查清单

- [ ] 设置强密码
- [ ] 绑定内网IP
- [ ] 禁用危险命令
- [ ] 使用 ACL 限制权限
- [ ] 启用 TLS/SSL(生产环境)
- [ ] 定期更新 Redis 版本
- [ ] 监控异常访问

---

## 7. 监控和运维

### 7.1 关键监控指标

```bash
# 内存使用
used_memory_human
used_memory_peak_human
maxmemory

# 命令执行
total_commands_processed
instantaneous_ops_per_sec

# 连接数
connected_clients

# 命中率
keyspace_hits
keyspace_misses
# 命中率 = hits / (hits + misses)
```

### 7.2 INFO 命令

```python
# 获取服务器信息
info = r.info()
print(info['used_memory_human'])
print(info['connected_clients'])
print(info['instantaneous_ops_per_sec'])

# 获取特定部分
info_server = r.info('server')
info_memory = r.info('memory')
info_stats = r.info('stats')
```

### 7.3 MONITOR 命令

⚠️ **注意**: MONITOR 会严重影响性能,仅用于调试

```bash
# 监控所有命令
MONITOR

# Python 中使用
for cmd in r.monitor():
    print(cmd)
```

### 7.4 监控工具推荐

- **Redis Insight**: 官方可视化工具
- **Prometheus + Grafana**: 指标监控和告警
- **Redis Exporter**: Prometheus 指标导出器
- **Redis Commander**: Web 管理界面

---

## 8. 测试环境配置

### 8.1 Docker Compose 配置

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7
    container_name: myredis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    environment:
      - REDIS_PASSWORD=your_password
    command: redis-server --requirepass your_password

  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: redis-commander
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOSTS=local:redis:6379:0:your_password

volumes:
  redis_data:
```

启动:

```bash
docker-compose up -d
```

连接测试:

```python
import redis

r = redis.Redis(
    host='localhost',
    port=6379,
    password='your_password',
    decode_responses=True
)

r.set('test', 'hello')
print(r.get('test'))  # 输出: hello
```

---

## 9. 常见问题 FAQ

### Q1: Redis 和 Memcached 的区别?

- Redis 支持更多数据类型,Memcached 只支持 String
- Redis 支持持久化,Memcached 不支持
- Redis 支持主从复制,Memcached 不支持
- Redis 单线程,Memcached 多线程

### Q2: 如何选择 Redis 数据类型?

- String: 简单值、计数器
- Hash: 对象、结构化数据
- List: 队列、栈、最新列表
- Set: 去重、集合运算
- Sorted Set: 排行榜、范围查询

### Q3: Redis 持久化方式?

- **RDB**: 快照,适合备份,恢复快
- **AOF**: 日志,数据更安全,恢复慢
- **混合**: RDB + AOF,推荐生产环境

### Q4: 如何解决 Redis 过期键删除?

- **惰性删除**: 访问时检查
- **定期删除**: 随机抽查删除

---

## 10. 参考资料

- [Redis 官方文档](https://redis.io/documentation)
- [redis-py 文档](https://redis-py.readthedocs.io/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Redis 命令参考](https://redis.io/commands)

---

**文档版本**: 1.0
**最后更新**: 2025-01-04
**维护者**: 开发团队
