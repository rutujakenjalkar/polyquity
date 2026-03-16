# Postgres Tool Module

import ast
import psycopg2
from psycopg2 import Error
import numpy as np


def execute_postgres_query(
	host: str,
	database: str,
	user: str,
	password: str,
	port: str,
	query: str,
	params: tuple | None = None,
) -> list[list]:
	connection = None
	try:
		connection = psycopg2.connect(
			host=host,
			database=database,
			user=user,
			password=password,
			port=port,
		)
		cursor = connection.cursor()
		cursor.execute(query, params)
		try:
			rows = cursor.fetchall()
		except psycopg2.ProgrammingError:
			rows = []
		connection.commit()
		cursor.close()
		return rows
	except Error as e:
		if connection:
			connection.rollback()
		raise
	finally:
		if connection:
			connection.close()

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
	print("this is has transactions rows")
	return bool(rows and rows[0] and rows[0][0])


def get_user_profile(
	host: str,
	database: str,
	user: str,
	password: str,
	port: str,
	wallet_address: str,
) -> dict:
	"""Main entry point for the postgres tool.
	
	Returns a dictionary with has_profile, profile_vector and purchased_ipo_ids.
	"""

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

	print("this is get user profile rows", rows,"\n")
	
	# separate ipo_ids and embeddings
	purchased_ipo_ids = [row[0] for row in rows]
	embeddings = [ast.literal_eval(row[1]) for row in rows]

	print(purchased_ipo_ids)
	print(embeddings)
	
	# aggregate embeddings into single profile vector using mean
	profile_vector = np.mean(embeddings, axis=0).tolist()

	return {
		"has_profile": True,
		"profile_vector": profile_vector,
		"purchased_ipo_ids": purchased_ipo_ids
	}
	



# small example showing usage
if __name__ == "__main__":
	try:
		wallet_address = "0x1a2b3c4d5e6f7890abcdef1234567890abcdef12"
		result = get_user_profile(
			host="localhost",
			database="POLYQUITY_DATA",
			user="postgres",
			password="rutuja",
			port="5432",
			wallet_address=wallet_address,
		)
		print("Result:", result)
	except Error as err:
		print("failed to run sample query:", err)

