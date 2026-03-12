import sqlite3

def login(username, password):
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    result = conn.execute(query)
    if result.fetchone():
        return True
    return False

def get_user_data(user_id):
    conn = sqlite3.connect("users.db")
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return conn.execute(query).fetchall()

SECRET_KEY = "hardcoded_secret_123"
API_TOKEN = "sk-prod-abc123xyz"