import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST"),
        user=os.getenv("MYSQLUSER"),
        password=os.getenv("MYSQLPASSWORD"),
        database=os.getenv("MYSQLDATABASE"),
        port = int(os.getenv("MYSQLPORT") or 3306))
    )

if __name__ == "__main__":
    conn = get_db_connection()
    print("CONECTADO 🚀")
    conn.close()
    