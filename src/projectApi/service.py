"""
用户模块 - 业务逻辑层
演示如何组织业务逻辑
"""
from typing import Any, AsyncIterator
from datetime import datetime
import json
import logging
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.crud import BaseCRUD
from src.projectApi.models import User
from src.demo.models import Item
from src.projectApi.schemas import UserCreate, UserResponse, UserUpdate
from src.common.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class UserCRUD(BaseCRUD[User, UserCreate, UserUpdate]):
    """用户 CRUD 操作类"""
    pass


# CRUD 实例
user_crud = UserCRUD(User)


# 业务逻辑函数

async def get_user_by_id(db: AsyncSession, user_id: int) -> dict[str, Any]:
    """
    根据 ID 获取用户
    """
    user = await user_crud.get(db=db, id=user_id)
    if not user:
        raise NotFoundException(detail=f"用户 {user_id} 不存在")
    return user


async def get_user_by_openid(db: AsyncSession, openid: str) -> dict[str, Any] | None:
    """
    根据微信 openid 获取用户
    """
    return await user_crud.get(db=db, openid=openid)

async def get_user_id(db: AsyncSession, user_id: int) -> dict[str, Any] | None:
    """
    根据用户ID获取用户及其关联的Item，返回字典或 None
    """
    result = await db.execute(
        select(User.nickname, Item.name).outerjoin(
            User, User.id == Item.id
        ).where(
            User.id == user_id
        )
    )
    
    result_handle = result.all()
    
    # 如果没有查询到数据，返回 None
    if not result_handle:
        return None
    
    # 提取第一条记录的用户昵称（所有记录的用户昵称相同）
    user_nickname = result_handle[0].nickname
    
    # 构建返回字典
    return {
        "nickname": user_nickname,
        "items": [
            {"item_name": row.name}
            for row in result_handle
        ],
        "item_count": len(result_handle)
    }

async def get_users(
    db: AsyncSession,
    offset: int = 0,
    limit: int = 10,
    status: int | None = None,
    is_active: bool | None = None,
    user_type: int | None = None,
) -> dict[str, Any]:
    """
    获取用户列表
    """
    filters = {}
    if status is not None:
        filters["status"] = status
    if is_active is not None:
        filters["is_active"] = is_active
    if user_type is not None:
        filters["user_type"] = user_type

    result = await user_crud.get_multi(
        db=db,
        offset=offset,
        limit=limit,
        **filters,
    )

    
    return result


async def create_user(db: AsyncSession, user_data: UserCreate) -> dict[str, Any]:
    """
    创建用户
    """
    return await user_crud.create_and_get(
        db=db,
        object=user_data,
        openid=user_data.openid,
    )


async def update_user(
    db: AsyncSession,
    user_id: int,
    user_data: UserUpdate,
) -> dict[str, Any]:
    """
    更新用户信息
    """
    # 先检查是否存在
    await get_user_by_id(db, user_id)

    # 过滤掉 None 值
    update_data = user_data.model_dump(exclude_unset=True)
    if update_data:
        await user_crud.update(db=db, object=update_data, id=user_id)


# ==========================================
# 原生 SQL 操作演示 - 核心知识点 3
# ==========================================
from sqlalchemy import text

async def create_user_raw(db: AsyncSession, user_data: UserCreate) -> dict[str, Any]:
    """
    创建用户
    """
    # 1. 定义插入语句
    # 注意：MySQL 不支持 RETURNING，我们需要分为插入和查询两步
    # 同时手动处理 created_at 和 updated_at，因为原生 SQL 不会触发 Python 层的默认值
    sql_insert = text("""
        INSERT INTO users (nickname, openid, user_type, status, is_active, created_at, updated_at)
        VALUES (:nickname, :openid, :user_type, :status, :is_active, NOW(), NOW())
    """)
    
    # 2. 执行插入
    result = await db.execute(sql_insert, {
        "nickname": user_data.nickname,
        "openid": user_data.openid,
        "user_type": user_data.user_type,
        "status": user_data.status,
        "is_active": user_data.is_active,
    })
    
    # 3. 获取刚刚生成的 ID (SQLAlchemy 异步模式下获取 lastrowid 的标准做法)
    inserted_id = result.lastrowid
    
    # 4. 查询并返回完整数据
    sql_select = text("SELECT * FROM users WHERE id = :uid")
    final_result = await db.execute(sql_select, {"uid": inserted_id})
    
    return dict(final_result.mappings().one())
    

async def get_user_stats_raw(db: AsyncSession, user_id: int) -> dict[str, Any]:
    """
    演示如何使用原生 SQL 执行复杂查询
    适用于：需要极高性能、使用数据库特有函数、或 ORM 难以表达的复杂 JOIN/聚合。
    """
    
    # 1. 定义原生 SQL 语句
    # 使用 :param_name 占位符防止 SQL 注入（核心安全知识）
    # 使用 text() 函数包装字符串
    sql_query = text("""
        SELECT 
            id, 
            nickname, 
            login_count,
            created_at,
            -- 这里演示数据库特有的逻辑（假设 MySQL）
            CASE 
                WHEN login_count > 10 THEN '活跃用户'
                WHEN login_count > 0 THEN '普通用户'
                ELSE '静默用户'
            END as user_level
        FROM users 
        WHERE id = :uid AND deleted_at IS NULL
    """)
    
    # 2. 执行查询
    # db.execute 是异步方法，必须 await
    # params 传入一个字典进行参数绑定
    result = await db.execute(sql_query, {"uid": user_id})
    
    # 3. 处理结果
    # 对于 SELECT 语句，.fetchone() 返回 Row 对象
    row = result.fetchone()
    
    if not row:
        return {}
    
    # 4. Row 对象转字典 (SQLAlchemy 2.0 常见操作)
    # Row 对象可以通过属性访问，也可以通过 _mapping 转换为字典
    return dict(row._mapping)


async def delete_user(db: AsyncSession, user_id: int) -> None:
    """
    删除用户（软删除）
    """
    # 先检查是否存在
    await get_user_by_id(db, user_id)
    
    # 软删除：设置 deleted_at
    await user_crud.update(
        db=db,
        object={"deleted_at": datetime.now()},
        id=user_id
    )


async def update_login_info(
    db: AsyncSession,
    user_id: int,
    login_ip: str | None = None,
) -> None:
    """
    更新用户登录信息
    """
    update_data = {
        "last_login_time": datetime.now(),
    }
    if login_ip:
        update_data["last_login_ip"] = login_ip
    
    # 如果是首次登录，设置 first_login_time
    user = await get_user_by_id(db, user_id)
    if user.get("first_login_time") is None:
        update_data["first_login_time"] = datetime.now()
    
    # 增加登录次数
    update_data["login_count"] = (user.get("login_count") or 0) + 1

    await user_crud.update(db=db, object=update_data, id=user_id)


# ==========================================
# Chat Agent 服务层
# ==========================================

# 简单的会话内存存储（生产环境应使用 Redis）
_session_memory: dict[str, list[dict]] = {}


class ChatAgentService:
    """Chat Agent 服务类"""

    def __init__(self):
        from src.agents.domains import register_all_domains
        from src.agents.core.factory import create_ems_agent
        from src.agents.core.workspace import WorkspaceManager

        # 注册所有领域 Agent
        register_all_domains()

        # 项目根目录
        self.project_root = os.path.abspath(os.getcwd())

    def _get_agent(self, user_id: str = "default_user"):
        """获取或创建 Agent 实例"""
        from src.agents.core.factory import create_ems_agent
        from src.agents.core.workspace import WorkspaceManager

        # 初始化工作区管理器
        workspace_mgr = WorkspaceManager(self.project_root, user_id)

        # 创建 Agent
        agent = create_ems_agent(user_id=user_id)

        return agent, workspace_mgr

    def _get_session_messages(self, session_id: str) -> list[dict]:
        """获取会话历史消息"""
        return _session_memory.get(session_id, [])

    def _save_session_message(self, session_id: str, role: str, content: str):
        """保存消息到会话历史"""
        if session_id not in _session_memory:
            _session_memory[session_id] = []

        _session_memory[session_id].append({
            "role": role,
            "content": content
        })

        # 限制历史记录数量（保留最近 20 条）
        if len(_session_memory[session_id]) > 20:
            _session_memory[session_id] = _session_memory[session_id][-20:]

    async def chat_stream(
        self,
        message: str,
        session_id: str | None = None,
        user_id: str = "default_user"
    ) -> AsyncIterator[dict]:
        """
        流式对话接口

        Args:
            message: 用户消息
            session_id: 会话ID
            user_id: 用户ID

        Yields:
            dict: 流式数据块
                {
                    "type": "token" | "error" | "done" | "metadata",
                    "content": str | None,
                    "metadata": dict | None,
                    "error": str | None,
                    "session_id": str | None
                }
        """
        import time

        # 生成新的 session_id
        if not session_id:
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:12]}"

        try:
            # 获取 Agent
            agent, workspace_mgr = self._get_agent(user_id)

            # 获取历史消息
            history = self._get_session_messages(session_id)

            # 构建消息列表
            messages = []
            for msg in history:
                messages.append((msg["role"], msg["content"]))
            messages.append(("user", message))

            # 发送会话ID
            yield {
                "type": "metadata",
                "content": None,
                "metadata": {"session_id": session_id},
                "session_id": session_id
            }

            start_time = time.time()
            full_response = ""

            # 流式调用 Agent
            async for step in agent.astream({"messages": messages}):
                if not isinstance(step, dict):
                    continue

                for node, values in step.items():
                    # 跳过中间件节点
                    if "Middleware" in node:
                        continue

                    if isinstance(values, dict) and "messages" in values:
                        msgs_obj = values.get("messages", [])
                        msgs = (
                            getattr(msgs_obj, "value", msgs_obj)
                            if not isinstance(msgs_obj, list)
                            else msgs_obj
                        )

                        if msgs:
                            last_msg = msgs[-1]
                            msg_class = last_msg.__class__.__name__

                            if msg_class == "AIMessage":
                                content = last_msg.content or ""

                                # 处理多模态消息
                                if isinstance(content, list):
                                    content = " ".join(
                                        block.get("text", "")
                                        for block in content
                                        if isinstance(block, dict) and block.get("type") == "text"
                                    )

                                if content.strip():
                                    # 发送 token
                                    yield {
                                        "type": "token",
                                        "content": content,
                                        "session_id": session_id
                                    }
                                    full_response = content

            # 保存到历史
            self._save_session_message(session_id, "user", message)
            self._save_session_message(session_id, "assistant", full_response)

            # 后台归档
            try:
                from src.agents.demo.multi_agent_demo import extract_and_archive_insights
                insights = await extract_and_archive_insights(message, full_response, workspace_mgr)

                yield {
                    "type": "metadata",
                    "content": f"\n📊 后台分析完成: {', '.join(insights)}",
                    "metadata": {"archived": True},
                    "session_id": session_id
                }
            except Exception as e:
                logger.warning(f"后台归档失败: {e}")

            # 计算耗时
            elapsed_time = time.time() - start_time

            # 发送完成信号
            yield {
                "type": "done",
                "content": None,
                "metadata": {
                    "elapsed_time": elapsed_time,
                    "response_length": len(full_response)
                },
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "session_id": session_id
            }


# 单例实例
chat_service = ChatAgentService()