import pyodbc

# ─── Update SERVER to match your SSMS server name ───────────
SERVER           = r'localhost\SQLEXPRESS'
DATABASE         = 'WorkforceIQ'
USE_WINDOWS_AUTH = True
USERNAME         = ''
PASSWORD         = ''
# ────────────────────────────────────────────────────────────

def get_connection():
    """Returns a live pyodbc connection to WorkforceIQ database."""
    try:
        if USE_WINDOWS_AUTH:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={SERVER};"
                f"DATABASE={DATABASE};"
                f"Trusted_Connection=yes;"
            )
        else:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={SERVER};"
                f"DATABASE={DATABASE};"
                f"UID={USERNAME};"
                f"PWD={PASSWORD};"
            )
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as e:
        print(f"[DB ERROR] Could not connect to SQL Server:\n{e}")
        return None


def test_connection():
    """Quick test to verify the connection works."""
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DB_NAME() AS DatabaseName, GETDATE() AS ServerTime")
        row = cursor.fetchone()
        print(f"[OK] Connected to: {row.DatabaseName}")
        print(f"[OK] Server Time:  {row.ServerTime}")
        conn.close()
    else:
        print("[FAILED] Connection unsuccessful.")


if __name__ == "__main__":
    test_connection()