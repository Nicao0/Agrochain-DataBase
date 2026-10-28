import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_SERVICE = os.getenv("DB_SERVICE")

def get_connection():
    try:
        dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"

        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=dsn
        )

        return conn

    except oracledb.Error as e:
        print(f"Erro ao conectar ao banco: {e}")
        return None