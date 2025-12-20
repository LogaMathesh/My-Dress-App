from werkzeug.security import check_password_hash
from config.database import cur, conn

def login_user(data):
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "Missing credentials"}, 400

    try:
        cur.execute(
            "SELECT password FROM users WHERE username = %s",
            (username,)
        )
        result = cur.fetchone()

        if result and check_password_hash(result[0], password):
            return {"message": "Login successful", "user": username}, 200

        return {"error": "Invalid credentials"}, 401

    except Exception as e:
        conn.rollback()
        return {"error": "Database error"}, 500
