from tools.cache import news_cache
import json


try:
    from tools.logger_utils import get_logger, set_run_id
except ImportError:
    from logger_utils import get_logger, set_run_id

logger = get_logger(__name__, "news_tool.log")


def news_tool(company_name: str, limit: int =10) -> str:
    """Return cached news headlines for a company as JSON."""
    try:
        logger.info("Starting news_tool for %s", company_name)
        headlines = news_cache.get(company_name, [])[:limit]
        logger.debug("Returned %d cached headlines for %s", len(headlines), company_name)
        return json.dumps(
            {
                "success": True,
                "company_name": company_name,
                "headline_count": len(headlines),
                "headlines": headlines,
            }
        )
    except Exception as e:
        logger.exception("news_tool failed for %s", company_name)
        return json.dumps(
            {
                "success": False,
                "company_name": company_name,
                "headline_count": 0,
                "headlines": [],
                "error": str(e),
            }
        )

'''
if __name__ == "__main__":
    set_run_id()
    print(news_tool("HDFC Bank"))
'''