import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="junction.proxy.rlwy.net",
        port=39867,
        user="root",
        password="38801233",
        database="railway"
    )

if __name__ == "__main__":
    conn = get_db_connection()
    print("CONECTADO 🚀")
    conn.close()
