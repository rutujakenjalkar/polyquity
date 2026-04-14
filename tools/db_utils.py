# Database Utility Module
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error

load_dotenv()

def execute_postgres_query(
    query: str = "SELECT ipo.ipo_id, ipo.name  FROM ipo JOIN transaction ON ipo.ipo_id = transaction.ipo_id ORDER BY net_profit DESC, revenue DESC LIMIT 5;",
    host: str = os.environ["POSTGRES_HOST"],
    database: str = os.environ["POSTGRES_DB"],
    user: str = os.environ["POSTGRES_USER"],
    password: str = os.environ["POSTGRES_PASSWORD"],
    port: str = os.environ["POSTGRES_PORT"],
    params: tuple | None = None,
) -> list[list]:
    """Connect to a PostgreSQL database and execute a query.

    This helper function opens a short-lived connection, runs the provided
    SQL statement, commits any changes and returns any result rows. It is
    intended for use against an *existing* table; the caller is responsible
    for supplying the correct connection parameters and an appropriate SQL
    query.

    Args:
        query: SQL statement to execute. May be a SELECT or an action query.
        host: hostname or IP of the Postgres server.
        database: database name to connect to.
        user: username.
        password: password for the user.
        port: port number (e.g. "5432").
        params: optional tuple of parameters to pass to ``cursor.execute``.

    Returns:
        A list of rows returned by the query. For non-SELECT statements an
        empty list is returned.

    Raises:
        :class:`psycopg2.Error` if the connection or execution fails.
    """

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

        # attempt to fetch results; non-SELECT statements raise
        try:
            rows = cursor.fetchall()
        except psycopg2.ProgrammingError:
            # no results to fetch
            rows = []

        connection.commit()
        cursor.close()
        return rows

    except Error as e:
        # rollback in case of error and re-raise
        if connection:
            connection.rollback()
        raise

    finally:
        if connection:
            connection.close()
