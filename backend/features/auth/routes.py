from flask import Blueprint, request, jsonify
from .service import login_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import cross_origin

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200   # ✅ preflight OK

    data = request.get_json()
    response, status = login_user(data)
    return jsonify(response), status

@auth_bp.route("/signup", methods=["POST", "OPTIONS"])
def signup():
    # Handle preflight explicitly
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    data = request.get_json(force=True)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing fields"}), 400

    from app import cur, conn  # temporary (we’ll clean this later)

    try:
        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password_hash),
        )
        conn.commit()
        return jsonify({"message": "Signup successful", "user": username}), 200
    except Exception:
        conn.rollback()
        return jsonify({"error": "Username already exists"}), 400