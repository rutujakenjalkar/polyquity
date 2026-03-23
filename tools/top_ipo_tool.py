# Top IPO Tool Module

from psycopg2 import Error
#from tools.db_utils import execute_postgres_query
import json
from db_utils import execute_postgres_query


def top_ipo_tool(query: str = "SELECT ipo.ipo_id, ipo.name FROM ipo JOIN transaction ON ipo.ipo_id = transaction.ipo_id ORDER BY net_profit DESC, revenue DESC LIMIT 5;") -> dict:
	"""Get top IPOs with error handling.
	Executes a query to fetch top IPOs and returns results with status.
	Args:
		query: SQL query to execute (uses default if not provided).
	Returns:
		Dictionary with success status, results, and optional error message.
	"""
    
	try:
		results = execute_postgres_query(
			query="SELECT ipo_id, name FROM ipo ORDER BY net_profit DESC, revenue DESC LIMIT 5;"
		)
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
		print(f"Database error in top_ipo_tool: {e}")
		return json.dumps({
			"success": False,
			"source": "cold_start",
			"candidates": [],
			"error": str(e)
		})


# Example usage; remove or adapt for real code
if __name__ == "__main__":
    print(top_ipo_tool())