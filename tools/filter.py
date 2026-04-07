# Cap Size Filter Tool

import json
from tools.db_utils import execute_postgres_query

def cap_size_filter_tool(cap_size: str) -> str:
    """Filter IPOs by market cap size — Large, Mid or Small."""
    try:
        # Validate input
        valid_sizes = ['Large', 'Mid', 'Small']
        cap_size = cap_size.strip().capitalize()
        
        if cap_size not in valid_sizes:
            return json.dumps({
                "success": False,
                "error": f"Invalid cap size. Choose from: {valid_sizes}"
            })

        results = execute_postgres_query(
            query="""
                SELECT  name
                FROM ipo
                WHERE cap_size = %s
                AND status IN ('upcoming', 'active')
                ORDER BY name ASC;
            """,
            params=(cap_size,)
        )
        print(results)

        if not results:
            return json.dumps({
                "success": True,
                "cap_size": cap_size,
                "companies": [],
                "message": f"No {cap_size} cap IPOs found currently"
            })

        companies = [
            {
                "name": row[0],
            }
            for row in results
        ]

        return json.dumps({
            "success": True,
            "cap_size": cap_size,
            "total": len(companies),
            "companies": companies
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        })


if __name__ == "__main__":

    print("Mid cap:", cap_size_filter_tool("Mid"))
    print("Small cap:", cap_size_filter_tool("Small"))