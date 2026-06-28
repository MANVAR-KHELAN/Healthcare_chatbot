import uuid

from flask import jsonify, redirect, render_template, request, session
from pymongo.errors import DuplicateKeyError
from werkzeug.security import generate_password_hash

from healthcare_chatbot.core.config import SUPPORTED_LANGUAGES
from healthcare_chatbot.utils.helpers import (
    iso_now,
    normalize_language,
    password_matches,
    set_authenticated_session,
)
from healthcare_chatbot.repositories import storage


def register_auth_routes(app):
    @app.route("/", methods=["GET"])
    def root():
        return redirect("/auth")

    @app.route("/auth", methods=["GET"])
    def auth_page():
        return render_template("auth.html", language=session.get("language"))

    @app.route("/experience", methods=["GET"])
    def experience():
        if not session.get("user_id"):
            return redirect("/auth")
        return render_template(
            "experience.html",
            language=session.get("language"),
            user_name=session.get("user_name"),
        )

    @app.route("/set_site_language", methods=["POST"])
    def set_site_language():
        data = request.json or {}
        language = normalize_language(data.get("language"))
        if language not in SUPPORTED_LANGUAGES:
            return jsonify({"success": False, "error": "Invalid language selection"}), 400
        session["language"] = language
        session.permanent = True
        return jsonify({"success": True, "language": language})

    @app.route("/signup", methods=["POST"])
    def signup():
        data = request.json or {}
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if len(name) < 2:
            return jsonify({"success": False, "error": "Name must be at least 2 characters"}), 400
        if "@" not in email or "." not in email:
            return jsonify({"success": False, "error": "Enter a valid email"}), 400
        if len(password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400
        if storage.find_user_by_email(email):
            return jsonify({"success": False, "error": "Email already exists"}), 400

        user = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "created_at": iso_now(),
        }
        try:
            storage.insert_user(user)
        except DuplicateKeyError:
            return jsonify({"success": False, "error": "Email already exists"}), 400

        set_authenticated_session(user)
        return jsonify({"success": True, "redirect": "/experience"})

    @app.route("/login", methods=["POST"])
    def login():
        data = request.json or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        user = storage.find_user_by_email(email)
        ok, matched_password = password_matches(user or {}, password)
        if not user or not ok:
            return jsonify({"success": False, "error": "Invalid email or password"}), 401

        if user.get("password") is not None and not user.get("password_hash"):
            storage.upgrade_legacy_password(
                user.get("id"),
                generate_password_hash(matched_password or password),
            )

        set_authenticated_session(user)
        session["language"] = normalize_language(session.get("language"), "english")
        return jsonify({"success": True, "redirect": "/experience"})

    @app.route("/logout", methods=["GET"])
    def logout():
        session.clear()
        return redirect("/auth")

