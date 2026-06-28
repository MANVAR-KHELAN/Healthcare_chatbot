from flask import jsonify

from healthcare_chatbot.core.config import MONGODB_DB_NAME
from healthcare_chatbot.utils.helpers import iso_now
from healthcare_chatbot.repositories import storage


def register_health_routes(app):
    @app.route("/api/health/db", methods=["GET"])
    def api_health_db():
        try:
            backend = storage.health_status()
            return jsonify({
                "success": True,
                "service": "healthcare-chatbot-api",
                "database": MONGODB_DB_NAME if backend == "mongo" else "local_json",
                "status": "ok",
                "backend": backend,
                "timestamp": iso_now(),
            }), 200
        except Exception as exc:
            return jsonify({
                "success": False,
                "service": "healthcare-chatbot-api",
                "database": MONGODB_DB_NAME,
                "status": "error",
                "error": str(exc),
                "timestamp": iso_now(),
            }), 503

    @app.route("/api/health/full", methods=["GET"])
    def api_health_full():
        try:
            backend = storage.health_status()
            users_count = storage.count_users()
            chats_count = storage.count_chat_messages()
            return jsonify({
                "success": True,
                "service": "healthcare-chatbot-api",
                "database": MONGODB_DB_NAME if backend == "mongo" else "local_json",
                "status": "ok",
                "backend": backend,
                "metrics": {
                    "users_count": users_count,
                    "chat_messages_count": chats_count,
                },
                "timestamp": iso_now(),
            }), 200
        except Exception as exc:
            return jsonify({
                "success": False,
                "service": "healthcare-chatbot-api",
                "database": MONGODB_DB_NAME,
                "status": "error",
                "error": str(exc),
                "timestamp": iso_now(),
            }), 503

