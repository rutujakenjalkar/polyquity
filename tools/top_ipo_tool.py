# Top IPO Tool Module

from psycopg2 import Error
from db_utils import execute_postgres_query


def top_ipo_tool(query: str = "SELECT ipo.ipo_id, ipo.embedding FROM ipo JOIN transaction ON ipo.ipo_id = transaction.ipo_id ORDER BY net_profit DESC, revenue DESC LIMIT 5;") -> dict:
	"""Get top IPOs with error handling.
	
	Executes a query to fetch top IPOs and returns results with status.
	
	Args:
		query: SQL query to execute (uses default if not provided).
	
	Returns:
		Dictionary with success status, results, and optional error message.
	"""
	try:
		results = execute_postgres_query(query=query)
		return {
			"success": True,
			"data": results,
			"error": None
		}
	except Error as e:
		print(f"Database error in top_ipo_tool: {e}")
		return {
			"success": False,
			"data": None,
			"error": str(e)
		}


# Example usage; remove or adapt for real code
if __name__ == "__main__":
    # Sample invocation, replace credentials/query as needed
    try:
        results = execute_postgres_query()
        print("Sample query returned:")
        for row in results:
            print(row)
    except Error as err:
        print("Failed to run sample query:", err)
