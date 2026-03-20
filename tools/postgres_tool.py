# Postgres Tool Module

import ast
import json
from psycopg2 import Error
import numpy as np
from tools.db_utils import execute_postgres_query

def wallet_has_transactions(
	host: str,
	database: str,
	user: str,
	password: str,
	port: str,
	wallet_address: str,
) -> bool:
	rows = execute_postgres_query(
		host=host,
		database=database,
		user=user,
		password=password,
		port=port,
		query="SELECT EXISTS (SELECT 1 FROM transaction WHERE wallet_address = %s);",
		params=(wallet_address,),
	)
	#print("this is has transactions rows")
	return bool(rows and rows[0] and rows[0][0])


def get_user_profile(wallet_address: str) -> dict:
	"""Main entry point for the postgres tool.
	
	Returns a dictionary with has_profile, profile_vector and purchased_ipo_ids.
	"""
	try:
		# Default connection parameters
		host = "localhost"
		database = "POLYQUITY_DATA"
		user = "postgres"
		password = "rutuja"
		port = "5432"

		has_transactions = wallet_has_transactions(
			host=host,
			database=database,
			user=user,
			password=password,
			port=port,
			wallet_address=wallet_address,
		)

		if not has_transactions:
			return {
				"has_profile": False,
				"profile_vector": None,
				"purchased_ipo_ids": []
			}

		# fetch embeddings and ipo_ids of purchased IPOs
		rows = execute_postgres_query(
			host=host,
			database=database,
			user=user,
			password=password,
			port=port,
			query=(
				"SELECT ipo.ipo_id, ipo.embedding FROM ipo JOIN transaction ON ipo.ipo_id = transaction.ipo_id WHERE transaction.wallet_address = %s;"
			),
			params=(wallet_address,),
		)

		#print("this is get user profile rows", rows,"\n")
		
		# separate ipo_ids and embeddings
		purchased_ipo_ids = [row[0] for row in rows]
		embeddings = [ast.literal_eval(row[1]) for row in rows]

		#print(purchased_ipo_ids)
		#print("embeddings:")
		#for i in embeddings:
		#	print(i,"\n")
		
		# aggregate embeddings into single profile vector using mean
		profile_vector = np.mean(embeddings, axis=0).tolist()

		return json.dumps({
			"has_profile": True,
			"profile_vector": profile_vector,
			"purchased_ipo_ids": purchased_ipo_ids
		})
	except Error as e:
		print(f"Database error in get_user_profile: {e}")
		return json.dumps({
			"has_profile": False,
			"profile_vector": None,
			"purchased_ipo_ids": [],
			"error": str(e)
		})
	


'''
# small example showing usage
if __name__ == "__main__":
	wallet_address = "0x1a2b3c4d5e6f7890abcdef1234567890abcdef12"
	result = get_user_profile(wallet_address)
	print( result)
'''
