import os
import json
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError

from healthcare_chatbot.core.config import (
    CHAT_HISTORY_FILE,
    USERS_FILE,
    MONGODB_URI,
    MONGODB_DB_NAME,
    MONGODB_USERS_COLLECTION,
    MONGODB_CHAT_COLLECTION,
)

mongo_client = None
db = None
users_collection = None
chat_history_collection = None


def _ensure_json_file(path):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as file:
            json.dump([], file)


def _read_json_list(path):
    _ensure_json_file(path)
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _uses_placeholder_mongo_uri(uri):
    marker_tokens = ["<username>", "<password>", "<cluster-url>", "<dbname>"]
    lowered = (uri or "").lower()
    return any(token in lowered for token in marker_tokens)


def _migrate_json_to_mongo():
    if users_collection is None or chat_history_collection is None:
        return
    if users_collection.estimated_document_count() == 0:
        users = _read_json_list(USERS_FILE)
        if users:
            users_collection.insert_many(users, ordered=False)
    if chat_history_collection.estimated_document_count() == 0:
        history = _read_json_list(CHAT_HISTORY_FILE)
        if history:
            chat_history_collection.insert_many(history, ordered=False)


def init_storage():
    global mongo_client, db, users_collection, chat_history_collection
    if not MONGODB_URI or _uses_placeholder_mongo_uri(MONGODB_URI):
        return

    try:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        mongo_client.admin.command("ping")
        db = mongo_client[MONGODB_DB_NAME]
        if MONGODB_USERS_COLLECTION not in db.list_collection_names():
            db.create_collection(MONGODB_USERS_COLLECTION)
        if MONGODB_CHAT_COLLECTION not in db.list_collection_names():
            db.create_collection(MONGODB_CHAT_COLLECTION)

        users_collection = db[MONGODB_USERS_COLLECTION]
        chat_history_collection = db[MONGODB_CHAT_COLLECTION]

        users_collection.create_index([("email", ASCENDING)], unique=True)
        chat_history_collection.create_index(
            [("user_id", ASCENDING), ("created_at", ASCENDING)]
        )
        chat_history_collection.create_index(
            [("conversation_id", ASCENDING), ("created_at", ASCENDING)]
        )
        _migrate_json_to_mongo()
    except Exception as exc:
        mongo_client = None
        db = None
        users_collection = None
        chat_history_collection = None
        print(f"[storage] MongoDB unavailable, using local JSON storage: {exc}")


def load_users():
    if users_collection is not None:
        return list(users_collection.find({}, {"_id": 0}))
    return _read_json_list(USERS_FILE)


def save_users(users):
    if users_collection is not None:
        users_collection.delete_many({})
        if users:
            users_collection.insert_many(users, ordered=False)
        return
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users or [], file, ensure_ascii=False, indent=2)


def find_user_by_email(email):
    normalized = (email or "").strip().lower()
    if users_collection is not None:
        user = users_collection.find_one({"email": normalized}, {"_id": 0})
        if user:
            return user
        for row in users_collection.find({}, {"_id": 0, "email": 1}):
            if (row.get("email") or "").strip().lower() == normalized:
                return users_collection.find_one({"email": row.get("email")}, {"_id": 0})
        for row in _read_json_list(USERS_FILE):
            if (row.get("email") or "").strip().lower() == normalized:
                try:
                    users_collection.update_one(
                        {"email": row.get("email")},
                        {"$setOnInsert": row},
                        upsert=True,
                    )
                except Exception:
                    pass
                return row
    users = load_users()
    for user in users:
        if (user.get("email") or "").strip().lower() == normalized:
            return user
    return None


def insert_user(user):
    if users_collection is not None:
        users_collection.insert_one(user)
        return
    users = load_users()
    if any((row.get("email") or "").strip().lower() == user["email"] for row in users):
        raise DuplicateKeyError("Email already exists")
    users.append(user)
    save_users(users)


def upgrade_legacy_password(user_id, password_hash):
    if users_collection is not None:
        users_collection.update_one(
            {"id": user_id},
            {
                "$set": {"password_hash": password_hash},
                "$unset": {"password": ""},
            },
        )
        return
    users = load_users()
    for row in users:
        if row.get("id") == user_id:
            row["password_hash"] = password_hash
            row.pop("password", None)
            break
    save_users(users)


def load_chat_history():
    if chat_history_collection is not None:
        return list(chat_history_collection.find({}, {"_id": 0}))
    return _read_json_list(CHAT_HISTORY_FILE)


def save_chat_history(records):
    if chat_history_collection is not None:
        chat_history_collection.delete_many({})
        if records:
            chat_history_collection.insert_many(records, ordered=False)
        return
    with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(records or [], file, ensure_ascii=False, indent=2)


def insert_chat_record(record):
    if chat_history_collection is not None:
        chat_history_collection.insert_one(record)
        return
    history = load_chat_history()
    history.append(record)
    save_chat_history(history)


def get_user_chat_records(user_id):
    if chat_history_collection is not None:
        return list(chat_history_collection.find({"user_id": user_id}, {"_id": 0}))
    history = load_chat_history()
    return [row for row in history if row.get("user_id") == user_id]


def health_status():
    if mongo_client is not None:
        mongo_client.admin.command("ping")
        return "mongo"
    return "json"


def count_users():
    if users_collection is not None:
        return users_collection.estimated_document_count()
    return len(load_users())


def count_chat_messages():
    if chat_history_collection is not None:
        return chat_history_collection.estimated_document_count()
    return len(load_chat_history())

