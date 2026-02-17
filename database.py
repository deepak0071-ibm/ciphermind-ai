import sqlite3

class DatabaseManager:

    def __init__(self):
        self.conn = sqlite3.connect("ciphermind.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            company TEXT
        )
        """)

    def save_lead(self, name, email, company):
        self.cursor.execute(
            "INSERT INTO leads (name, email, company) VALUES (?, ?, ?)",
            (name, email, company)
        )
        self.conn.commit()

    def get_leads(self):
        self.cursor.execute("SELECT * FROM leads")
        return self.cursor.fetchall()
