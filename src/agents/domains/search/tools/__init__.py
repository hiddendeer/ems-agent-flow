"""
电力情报搜索工具 — 使用 Tavily AI 搜索引擎。

注：
1. 需要在 .env 中配置 TAVILY_API_KEY
2. 如果未配置 API Key，将回退到模拟搜索以保证系统可用。
"""

from langchain_core.tools import tool
from tavily import TavilyClient
from ....config.settings import settings
from ....core.resilience import timeout_fallback
import logging

logger = logging.getLogger(__name__)

# 初始化客户端
def _get_tavily_client():
    if not settings.TAVILY_API_KEY:
        logger.warning("⚠️ TAVILY_API_KEY 未配置，将使用模拟数据。")
        return None
    return TavilyClient(api_key=settings.TAVILY_API_KEY)

@tool
@timeout_fallback(timeout_seconds=15)
def internet_search_power_policy(query: str) -> str:
    """
    通过 Tavily 搜索最新的电力、储能、双碳相关政策文件。
    :param query: 搜索关键词
    """
    client = _get_tavily_client()
    if not client:
        return (
            f"【模拟搜索 - 请配置 TAVILY_API_KEY】关于 '{query}'：\n"
            "1. 国家能源局近日发布《电力市场运行规则（征求意见稿）》，强调各类新型主体参与调峰。\n"
            "2. 广东省发改委最新《2024年电力现货市场准入规定》正式施行。"
        )
    
    try:
        # 执行搜索
        # 使用 basic 模式平衡速度与质量
        response = client.search(
            query=f"电力 储能 政策 {query}",
            search_depth="basic",
            max_results=5,
            include_raw_content=False
        )
        
        results = []
        for i, r in enumerate(response.get("results", []), 1):
            results.append(f"{i}. [{r['title']}]({r['url']})\n   摘要: {r['content'][:200]}...")
            
        return f"🔍 Tavily 电力政策搜索结果：\n\n" + "\n\n".join(results)
    
    except Exception as e:
        return f"❌ Tavily 搜索失败: {str(e)}"

@tool
@timeout_fallback(timeout_seconds=15)
def search_market_research_reports(topic: str) -> str:
    """
    通过 Tavily 搜索电力行业的研究报告摘要。
    :param topic: 报告主题
    """
    client = _get_tavily_client()
    if not client:
        return f"【模拟搜索结果】主题 '{topic}'：\n- 《2025全球长时储能白皮书》：预计中国市场 CAGR 超过 45%。"

    try:
        # 针对研报搜索优化 query
        response = client.search(
            query=f"{topic} 电力行业 研究报告 研报 市场分析",
            search_depth="basic",
            max_results=3
        )
        
        results = []
        for i, r in enumerate(response.get("results", []), 1):
            results.append(f"📊 [{r['title']}]({r['url']})\n   {r['content'][:300]}...")
            
        return f"📈 行业研报检索结果：\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"❌ 研报搜索失败: {str(e)}"

@tool
@timeout_fallback(timeout_seconds=15)
def track_competitor_dynamics(company_name: str) -> str:
    """
    通过 Tavily 追踪竞争对手（如宁德时代, 特斯拉, 阳光电源）的最新业务动态。
    :param company_name: 公司名称
    """
    client = _get_tavily_client()
    if not client:
        return f"【模拟动态】{company_name} 最新动态：获得了北美大型独立供电商的 3GWh 订单。"

    try:
        response = client.search(
            query=f"{company_name} 最新新闻 业务动态 订单 投产",
            search_depth="basic",
            max_results=3
        )
        
        results = []
        for r in response.get("results", []):
            results.append(f"📌 {r['title']}\n   {r['content'][:150]}...")
            
        return f"🏢 {company_name} 竞争情报追踪：\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"❌ 竞对追踪失败: {str(e)}"
