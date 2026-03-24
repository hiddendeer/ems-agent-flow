"""
用户模块 - Pydantic 模型（Schema）
演示请求和响应模型的定义
"""
from datetime import datetime
from typing import Any

from pydantic import Field, EmailStr

from src.common.schemas import CustomModel


class UserBase(CustomModel):
    """用户基础模型"""
    openid: str = Field(..., min_length=1, max_length=64, description="微信openid")
    unionid: str | None = Field(None, max_length=64, description="微信unionid")
    session_key: str | None = Field(None, max_length=64, description="微信session_key")
    
    nickname: str | None = Field(None, max_length=100, description="用户昵称")
    avatar_url: str | None = Field(None, max_length=500, description="用户头像URL")
    gender: int = Field(0, ge=0, le=2, description="性别：0-未知，1-男，2-女")
    
    country: str | None = Field(None, max_length=50, description="国家")
    province: str | None = Field(None, max_length=50, description="省份")
    city: str | None = Field(None, max_length=50, description="城市")
    language: str = Field("zh_CN", max_length=20, description="语言")
    
    phone_number: str | None = Field(None, max_length=20, description="手机号")
    country_code: str = Field("+86", max_length=10, description="国家区号")


class UserCreate(UserBase):
    """创建用户请求模型"""
    pass


class UserUpdate(CustomModel):
    """更新用户请求模型（所有字段可选）"""
    openid: str | None = Field(None, min_length=1, max_length=64, description="微信openid")
    unionid: str | None = Field(None, max_length=64, description="微信unionid")
    session_key: str | None = Field(None, max_length=64, description="微信session_key")
    
    nickname: str | None = Field(None, max_length=100, description="用户昵称")
    avatar_url: str | None = Field(None, max_length=500, description="用户头像URL")
    gender: int | None = Field(None, ge=0, le=2, description="性别：0-未知，1-男，2-女")
    
    country: str | None = Field(None, max_length=50, description="国家")
    province: str | None = Field(None, max_length=50, description="省份")
    city: str | None = Field(None, max_length=50, description="城市")
    language: str | None = Field(None, max_length=20, description="语言")
    
    phone_number: str | None = Field(None, max_length=20, description="手机号")
    country_code: str | None = Field(None, max_length=10, description="国家区号")
    
    is_active: bool | None = Field(None, description="是否激活")
    is_verified: bool | None = Field(None, description="是否实名认证")
    user_type: int | None = Field(None, ge=1, description="用户类型")
    status: int | None = Field(None, ge=0, le=2, description="账号状态")
    
    register_source: str | None = Field(None, max_length=20, description="注册来源")
    last_login_ip: str | None = Field(None, max_length=50, description="最后登录IP")


class UserResponse(UserBase):
    """用户响应模型"""
    id: int = Field(..., description="用户ID")
    
    is_active: bool = Field(True, description="是否激活")
    is_verified: bool = Field(False, description="是否实名认证")
    user_type: int = Field(1, description="用户类型")
    status: int = Field(1, description="账号状态")
    
    register_source: str = Field("miniprogram", description="注册来源")
    first_login_time: datetime | None = Field(None, description="首次登录时间")
    last_login_time: datetime | None = Field(None, description="最后登录时间")
    login_count: int = Field(0, description="登录次数")
    last_login_ip: str | None = Field(None, description="最后登录IP")
    
    extra_info: dict | None = Field(None, description="扩展信息")
    
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    deleted_at: datetime | None = Field(None, description="删除时间")


class UserListResponse(CustomModel):
    """用户列表响应模型"""
    data: list[UserResponse] = Field(default_factory=list, description="用户列表")
    total: int = Field(0, description="总数")


class UserLoginRequest(CustomModel):
    """用户登录请求模型"""
    code: str = Field(..., min_length=1, description="微信登录 code")
    encrypted_data: str | None = Field(None, description="加密数据")
    iv: str | None = Field(None, description="加密向量")


class UserLoginResponse(CustomModel):
    """用户登录响应模型"""
    user_id: int = Field(..., description="用户ID")
    openid: str = Field(..., description="微信openid")
    is_new: bool = Field(False, description="是否为新用户")
    session_key: str | None = Field(None, description="会话密钥")
    access_token: str | None = Field(None, description="访问令牌")


# ==========================================
# Chat 对话相关模型
# ==========================================

class ChatMessage(CustomModel):
    """单条聊天消息"""
    role: str = Field(..., description="角色：user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: datetime | None = Field(None, description="时间戳")


class ChatRequest(CustomModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, max_length=5000, description="用户消息内容")
    session_id: str | None = Field(None, description="会话ID，用于多轮对话上下文")
    user_id: str | None = Field("default_user", description="用户ID")
    stream: bool = Field(True, description="是否使用流式输出")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "帮我查询江苏最新的分时电价政策",
                "session_id": "session_123",
                "user_id": "user_001",
                "stream": True
            }
        }


class ChatStreamChunk(CustomModel):
    """流式响应数据块"""
    type: str = Field(..., description="块类型：token/error/done/metadata")
    content: str | None = Field(None, description="内容片段")
    metadata: dict | None = Field(None, description="元数据信息")
    error: str | None = Field(None, description="错误信息")
    session_id: str | None = Field(None, description="会话ID")

