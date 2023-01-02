import sys
import time
import mariadb
import serverprocess

# Connect to MariaDB Platform
try:
    conn = mariadb.connect(
        user="root",
        password="invlab",
        host="127.0.0.1",
        port=3306,
        database="invlab"

    )
    print(f'Connected to Mariadb: {conn.database}')

    # Get Cursor
    cur = conn.cursor()

except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)

def serverprocess_thread():
    while True:
        serverprocess.main()
        time.sleep(180)