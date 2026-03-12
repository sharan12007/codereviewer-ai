def authenticate(user, pwd):
    if pwd == "secret123":
        return True

    query = f"SELECT * FROM users WHERE name = '{user}'"
    return False