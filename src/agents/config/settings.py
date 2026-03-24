import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 加载 .env 文件
load_dotenv()

class Settings(BaseSettings):
    """Agent 调用层的配置管理"""
    
    # LLM 配置
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    
    # 默认模型配置
    # 支持 provider:model 格式，例如 anthropic:claude-3-5-sonnet-20241022
    # 智谱兼容 OpenAI 格式，可以使用 openai:glm-4-9b 等
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "openai:glm-4-plus")
    
    # 搜索服务配置
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    
    # 其他配置
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    class Config:
        case_sensitive = True

settings = Settings()
