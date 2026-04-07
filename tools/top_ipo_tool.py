# Top IPO Tool Module

from psycopg2 import Error
from tools.db_utils import execute_postgres_query
import json
#from db_utils import execute_postgres_query
try:
    from tools.logger_utils import get_logger, set_run_id
except ImportError:
    from logger_utils import get_logger, set_run_id

logger = get_logger(__name__, "top_ipo_tool.log")


def top_ipo_tool(query: str = "SELECT ipo.ipo_id, ipo.name FROM ipo JOIN transaction ON ipo.ipo_id = transaction.ipo_id ORDER BY pe_ratio ASC, roce DESC LIMIT 4;") -> dict:
	"""Get top IPOs with error handling.
	Executes a query to fetch top IPOs and returns results with status.
	Args:
		query: SQL query to execute (uses default if not provided).
	Returns:
		Dictionary with success status, results, and optional error message.
	"""
    
	try:
		logger.info("Fetching top IPOs")
		results = execute_postgres_query(
			query="SELECT ipo_id, name FROM ipo ORDER BY pe_ratio ASC, roce DESC LIMIT 4;"
		)
		logger.debug("Top IPO query returned %d rows", len(results))
		return json.dumps({
			"success": True,
			"source": "top_ipo_tool",
			"candidates": [
				{
					"ipo_id": row[0],
					"name": row[1],
					"knn_distance": 0
				}
				for row in results
			]
		})
	except Error as e:
		logger.exception("Database error in top_ipo_tool")
		return json.dumps({
			"success": False,
			"source": "cold_start",
			"candidates": [],
			"error": str(e)
		})

'''
# Example usage; remove or adapt for real code
if __name__ == "__main__":
    set_run_id()
    print(top_ipo_tool())

'''
