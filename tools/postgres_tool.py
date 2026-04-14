# Postgres Tool Module
import os
from dotenv import load_dotenv
import ast
import json
from psycopg2 import Error
import numpy as np
from tools.db_utils import execute_postgres_query

load_dotenv()
#from db_utils import execute_postgres_query
try:
	from tools.logger_utils import get_logger, set_run_id
except ImportError:
	from logger_utils import get_logger, set_run_id

logger = get_logger(__name__, "postgres_tool.log")

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
	logger.debug("Checked transaction history for wallet %s", wallet_address)
	return bool(rows and rows[0] and rows[0][0])


def get_user_profile(wallet_address: str) -> dict:
	"""Main entry point for the postgres tool.
	
	Returns a dictionary with has_profile, profile_vector and purchased_ipo_ids.
	"""
	try:
		logger.info("Starting get_user_profile for wallet %s", wallet_address)

		has_transactions = wallet_has_transactions(
			host=os.environ["POSTGRES_HOST"],
			database= os.environ["POSTGRES_DB"],
			user= os.environ["POSTGRES_USER"],
			password=os.environ["POSTGRES_PASSWORD"],
			port=os.environ["POSTGRES_PORT"],
			wallet_address=wallet_address,
		)

		if not has_transactions:
			logger.info("No transaction history found for wallet %s", wallet_address)
			return {
				"has_profile": False,
				"profile_vector": None,
				"purchased_ipo_ids": []
			}

		# fetch embeddings and ipo_ids of purchased IPOs
		rows = execute_postgres_query(
			query=(
				"SELECT ipo.ipo_id, ipo.embedding FROM ipo JOIN transaction ON ipo.ipo_id = transaction.ipo_id WHERE transaction.wallet_address = %s;"
			),
			params=(wallet_address,),
		)
		logger.debug("Fetched %d purchased IPO rows for wallet %s", len(rows), wallet_address)

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
		logger.info("Built profile vector for wallet %s", wallet_address)

		return json.dumps({
			"has_profile": True,
			"profile_vector": profile_vector,
			"purchased_ipo_ids": purchased_ipo_ids
		})
	except Error as e:
		logger.exception("Database error in get_user_profile for wallet %s", wallet_address)
		return json.dumps({
			"has_profile": False,
			"profile_vector": None,
			"purchased_ipo_ids": [],
			"error": str(e)
		})
	




'''
# small example showing usage
if __name__ == "__main__":
	print(set_run_id())
	wallet_address = "0x1234567890ABCDEF1234567890ABCDEF12345678"
	result = get_user_profile(wallet_address)
	print( result)
'''