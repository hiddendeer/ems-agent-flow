"""
MySQL 学习模块 - 初始化数据库（建表脚本）
"""
import asyncio
import sys
import os

# 将项目根目录添加到路径，确保可以导入 src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.projectApi.db import engine, Base
from src.projectApi.models_learning import LearningTask 
from src.projectApi.models_business import User, Family, FamilyMember, Device # 导入新业务模型

async def init_db():
    print("正在连接 MySQL...")
    try:
        async with engine.begin() as conn:
            # 这一步会根据定义的模型在数据库中创建所有不存在的表
            print("正在创建表...")
            await conn.run_sync(Base.metadata.create_all)
            print("表创建成功！")
            
            # 测试插入一条数据
            print("数据库连接并建表成功，你现在可以开始学习 MySQL 语法了。")
            
    except Exception as e:
        print(f"初始化数据库失败: {e}")
        print("\n提示：请确保你已经在 MySQL 中创建了数据库 'project_api_test'")
        print("执行命令: CREATE DATABASE project_api_test CHARACTER SET utf8mb4;")

if __name__ == "__main__":
    asyncio.run(init_db())
