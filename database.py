import sqlite3

def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            email TEXT,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
