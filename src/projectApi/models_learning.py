"""
MySQL 学习模块 - 数据库模型示例
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class LearningTask(Base):
    """
    学习任务表模型
    演示基本的 SQLAlchemy 映射
    """
    __tablename__ = "learning_tasks"

    # Mapped[type] 定义类型，mapped_column 定义数据库列属性
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title: Mapped[str] = mapped_column(String(100), nullable=False, comment="任务标题")
    content: Mapped[str | None] = mapped_column(Text, default=None, comment="任务内容")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否完成")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self) -> str:
        return f"<LearningTask(title='{self.title}', completed={self.is_completed})>"
