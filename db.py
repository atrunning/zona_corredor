import mysql.connector
import os

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQLHOST", "127.0.0.1"),
        user=os.getenv("MYSQLUSER", "root"),
        password=os.getenv("MYSQLPASSWORD", "Jdro3807"),
        database=os.getenv("MYSQLDATABASE", "atrunning"),
        port=int(os.getenv("MYSQLPORT", 3306))
    )

if __name__ == "__main__":
    conn = get_db_connection()
    print("CONECTADO 🚀")
    conn.close()

if __name__ == "__main__":
    conn = get_db_connection()
    print("CONECTADO 🚀")
    conn.close()
    