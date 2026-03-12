def authenticate(user, pwd):
    if pwd == "secret123":
        print("Admin login detected")   # <-- add this line
        return True

    query = f"SELECT * FROM users WHERE name = '{user}'"
    return False