import hashlib
import hmac
import os
import re
import uuid
from datetime import datetime

from flask import session, url_for
from werkzeug.security import check_password_hash

from healthcare_chatbot.core.config import LANGUAGE_ALIASES, MOJIBAKE_HINTS
from healthcare_chatbot.repositories import storage


def static_asset_version(static_root, filename):
    asset_path = os.path.join(static_root, filename)
    try:
        return int(os.path.getmtime(asset_path))
    except OSError:
        return int(datetime.utcnow().timestamp())


def inject_static_asset(app):
    static_root = app.static_folder or "static"

    def static_asset(filename):
        return url_for("static", filename=filename, v=static_asset_version(static_root, filename))

    return {"static_asset": static_asset}


def iso_now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def strip_html(text):
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def normalize_language(language, default=None):
    raw = (language or "").strip().lower()
    if not raw:
        return default
    return LANGUAGE_ALIASES.get(raw, default)


def language_text(language, texts, default="english"):
    return texts.get(language, texts.get(default, ""))


def repair_mojibake(text):
    if not isinstance(text, str) or not text:
        return text

    if not any(token in text for token in MOJIBAKE_HINTS):
        return text

    candidates = [text]
    for src in ("latin-1", "cp1252"):
        try:
            candidates.append(text.encode(src).decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue

    def score(value):
        return sum(value.count(token) for token in MOJIBAKE_HINTS)

    return min(candidates, key=score)


def check_scrypt_hash(stored_hash, password):
    try:
        method, salt, expected = stored_hash.split("$", 2)
        if not method.startswith("scrypt:"):
            return False
        parts = method.split(":")
        if len(parts) != 4:
            return False
        n = int(parts[1])
        r = int(parts[2])
        p = int(parts[3])
        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            n=n,
            r=r,
            p=p,
        ).hex()
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


def password_matches(user, password):
    pwd = password or ""
    pwd_stripped = pwd.strip()
    candidates = [pwd]
    if pwd_stripped != pwd:
        candidates.append(pwd_stripped)

    stored_hash = user.get("password_hash") or ""
    if stored_hash:
        for candidate in candidates:
            try:
                if check_password_hash(stored_hash, candidate):
                    return True, candidate
            except (ValueError, TypeError):
                if check_scrypt_hash(stored_hash, candidate):
                    return True, candidate
                break

    legacy_password = user.get("password")
    if isinstance(legacy_password, str):
        for candidate in candidates:
            if legacy_password == candidate:
                return True, candidate

    return False, None


def set_authenticated_session(user):
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    session["has_seen_dashboard"] = False
    session.permanent = True
    start_new_conversation()


def validate_age(age):
    if age is None or (isinstance(age, str) and not age.strip()):
        return None
    try:
        age_val = int(age)
    except (ValueError, TypeError):
        return None
    return age_val if 1 <= age_val <= 120 else None


def init_session_defaults():
    defaults = {
        "messages": [],
        "language": None,
        "gender": None,
        "age": None,
    }
    for key, value in defaults.items():
        if key not in session:
            session[key] = value
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
    if "conversation_id" not in session:
        session["conversation_id"] = str(uuid.uuid4())
    if "user_id" not in session:
        session["user_id"] = None
    if "user_name" not in session:
        session["user_name"] = None
    if "user_email" not in session:
        session["user_email"] = None
    if "has_seen_dashboard" not in session:
        session["has_seen_dashboard"] = False

    normalized_language = normalize_language(session.get("language"), "english")
    if session.get("language") != normalized_language:
        session["language"] = normalized_language
        session.modified = True


def is_logged_in():
    return bool(session.get("user_id"))


def log_message(role, content, message_type="chat"):
    init_session_defaults()
    content = repair_mojibake(content)
    timestamp = iso_now()
    message = {
        "role": role,
        "content": content,
        "created_at": timestamp,
        "message_type": message_type,
    }
    session["messages"].append(message)
    session.modified = True

    storage.insert_chat_record({
        "user_id": session.get("user_id"),
        "user_name": session.get("user_name"),
        "user_email": session.get("user_email"),
        "session_id": session["session_id"],
        "conversation_id": session["conversation_id"],
        "role": role,
        "content": content,
        "content_text": strip_html(content),
        "language": session.get("language"),
        "gender": session.get("gender"),
        "age": session.get("age"),
        "message_type": message_type,
        "created_at": timestamp,
    })


def start_new_conversation():
    session["conversation_id"] = str(uuid.uuid4())
    session["messages"] = []
    session.modified = True


def keyword_count(text, keywords):
    lowered = (text or "").lower()
    return sum(1 for word in keywords if word in lowered)


def format_response(response, language="english"):
    response = repair_mojibake(response or "")
    language = normalize_language(language, "english")

    response = re.sub(r"<Thinking>.*?</Thinking>", "", response, flags=re.DOTALL)
    response = re.sub(
        r"^.*?(Alright|Okay|Let's|First|Looking|Now|So|Wait|I'll|I need to).*$\n?",
        "",
        response,
        flags=re.MULTILINE,
    )

    response = re.sub(r"\n{3,}", "\n\n", response)
    response = re.sub(r"###\s*(.*?)\s*\n", r"<h3>\1</h3>", response)
    response = re.sub(r"##\s*(.*?)\s*\n", r"<h2>\1</h2>", response)
    response = re.sub(r"#\s*(.*?)\s*\n", r"<h1>\1</h1>", response)

    response = re.sub(r"\n\s*(?:\*|-|\u2022)\s*", "\n<li>", response)
    response = re.sub(r"\n\s*(\d+)\.\s*", r"\n<li><strong>\1.</strong> ", response)
    response = re.sub(r"<li>(.*?)(?=\n<li>|\n*$)", r"<li>\1</li>", response, flags=re.DOTALL)
    if "<li>" in response:
        response = re.sub(r"(<li>.*?</li>)", r"<ul>\1</ul>", response, flags=re.DOTALL)

    response = f'<div class="formatted-response">{response.strip()}</div>'
    return repair_mojibake(response)

