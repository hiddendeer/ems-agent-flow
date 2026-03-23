from datetime import datetime
import platform
import os
from langchain_core.tools import tool

@tool
def get_system_info() -> str:
    """获取系统基础信息，如操作系统版本、Python 版本。"""
    info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "python_version": platform.python_version()
    }
    return f"System Info: {info}"

@tool
def simulated_search(query: str) -> str:
    """
    模拟一个搜索引擎。用于查询实时的外部数据（如电价、政策等）。
    :param query: 搜索关键词
    """
    return f"【模拟搜索检索结果】关于'{query}'：最新广东省工业用电价格分为三个时段：高峰时段约为1.15元/千瓦时，平段约为0.65元/千瓦时，低谷时段约为0.32元/千瓦时。当前电力规程要求重点保障工业企业用电平稳，并鼓励错峰用电以降低成本。"

@tool
def write_to_file(filename: str, content: str) -> str:
    """
    将内容写入到指定的文件路径中。
    :param filename: 文件路径 (如 'src/agents/demo/reports/report_20240101.md')
    :param content: 要保存的文本内容
    :return: 执行结果消息
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully saved to {filename}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@tool
def get_current_time() -> str:
    """获取当前的系统日期和时间，用于文件名。格式：YYYYMMDD_HHMMSS"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
