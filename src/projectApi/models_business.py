"""
业务模块 - 用户、家庭与设备模型设计
"""
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Text, Boolean, JSON, ForeignKey, Date, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class User(Base):
    """
    用户主表：存储核心档案与偏好
    """
    __tablename__ = "app_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户唯一ID")
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="登录账号")
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户名称/昵称")
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, comment="手机号")
    
    # 基础档案
    gender: Mapped[int] = mapped_column(SmallInteger, default=0, comment="性别：0-未知, 1-男, 2-女")
    birthday: Mapped[Optional[date]] = mapped_column(Date, nullable=True, comment="出生日期")
    signature: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, comment="个性签名")
    
    # 账号绑定 (存储第三方ID，不为空代表已绑定)
    wechat_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="微信账号ID")
    apple_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="苹果账号ID")
    
    # 偏好标签 (使用 JSON 存储，方便扩展标签类型)
    # 格式示例: {"scenes": ["睡眠质量", "节能"], "devices": ["空气净化器"]}
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="偏好标签：场景与设备")
    
    # 状态与备注
    account_status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="状态：0-禁用, 1-正常, 2-已注销")
    admin_remark: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, comment="后台管理员备注")
    
    registration_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="注册时间")
    last_login_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后登录时间")

    # 关系映射
    memberships: Mapped[List["FamilyMember"]] = relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"<User(nickname='{self.nickname}', username='{self.username}')>"

class Family(Base):
    """
    家庭表
    """
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="家庭名称")
    creator_id: Mapped[int] = mapped_column(ForeignKey("app_users.id"), comment="创建者ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 关系映射
    members: Mapped[List["FamilyMember"]] = relationship(back_populates="family")
    devices: Mapped[List["Device"]] = relationship(back_populates="family")

    def __repr__(self) -> str:
        return f"<Family(name='{self.name}')>"

class FamilyMember(Base):
    """
    家庭成员关联表 (用户 <-> 家庭)
    """
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("app_users.id"), nullable=False)
    
    member_nickname: Mapped[Optional[str]] = mapped_column(String(50), comment="家庭成员昵称")
    role: Mapped[int] = mapped_column(SmallInteger, default=3, comment="权限：1-创建者, 2-管理员, 3-普通成员")
    relationship_remark: Mapped[Optional[str]] = mapped_column(String(50), comment="关系备注(如：父亲)")
    
    community_status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="社区状态：1-正常, 0-禁言")
    join_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # 关系映射
    user: Mapped["User"] = relationship(back_populates="memberships")
    family: Mapped["Family"] = relationship(back_populates="members")

class Device(Base):
    """
    设备表
    """
    __tablename__ = "family_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(ForeignKey("families.id"), nullable=False)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="自定义设备名称")
    product_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="产品类型名称")
    mac_address: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="云端唯一标识")
    
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, comment="在线状态")
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="激活/绑定时间")

    # 关系映射
    family: Mapped["Family"] = relationship(back_populates="devices")

    def __repr__(self) -> str:
        return f"<Device(name='{self.name}', mac='{self.mac_address}')>"
