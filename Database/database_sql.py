import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

_conn = None

def get_sql_connection():
    global _conn
    if _conn is None:
        _conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.getenv('SQL_SERVER')},1433;"
            f"DATABASE={os.getenv('SQL_DB')};"
            f"UID={os.getenv('SQL_USER')};"
            f"PWD={os.getenv('SQL_PASSWORD')};"
            f"Encrypt=no;"
            f"TrustServerCertificate=yes;"
        )
    return _conn
