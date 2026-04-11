# Cap Size Filter Tool

import json
from tools.db_utils import execute_postgres_query
from tools.logger_utils import get_logger

logger = get_logger(__name__, "cap_size_filter_tool.log")


def cap_size_filter_tool(cap_size: str) -> str:
    """Filter IPOs by market cap size - Large, Mid or Small."""
    raw_cap_size = cap_size
    try:
        logger.info("Starting cap_size_filter_tool with raw input: %s", raw_cap_size)

        valid_sizes = ["Large", "Mid", "Small"]
        cap_size = cap_size.strip().capitalize()
        logger.debug("Normalized cap_size input to: %s", cap_size)

        if cap_size not in valid_sizes:
            logger.warning("Invalid cap_size received: %s", cap_size)
            return json.dumps({
                "success": False,
                "error": f"Invalid cap size. Choose from: {valid_sizes}"
            })

        results = execute_postgres_query(
            query="""
                SELECT name
                FROM ipo
                WHERE cap_size = %s
                AND status IN ('upcoming', 'active')
                ORDER BY name ASC;
            """,
            params=(cap_size,)
        )
        logger.info(
            "cap_size_filter_tool query completed for %s with %d result(s)",
            cap_size,
            len(results),
        )

        if not results:
            logger.info("No companies found for cap_size=%s", cap_size)
            return json.dumps({
                "success": True,
                "cap_size": cap_size,
                "companies": [],
                "message": f"No {cap_size} cap IPOs found currently"
            })

        companies = [{"name": row[0]} for row in results]
        logger.info("Returning %d companies for cap_size=%s", len(companies), cap_size)

        return json.dumps({
            "success": True,
            "cap_size": cap_size,
            "total": len(companies),
            "companies": companies
        })

    except Exception as e:
        logger.exception("cap_size_filter_tool failed for raw input: %s", raw_cap_size)
        return json.dumps({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":
    print("Mid cap:", cap_size_filter_tool("Mid"))
    print("Small cap:", cap_size_filter_tool("Small"))
