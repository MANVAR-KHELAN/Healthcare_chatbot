import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

DATA_FOLDER = "data"
UPLOAD_FOLDER = "uploads"
CHAT_HISTORY_FILE = os.path.join(DATA_FOLDER, "chat_history.json")
USERS_FILE = os.path.join(DATA_FOLDER, "users.json")

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
GROQ_API_KEY = (os.getenv("GROQ_API_KEY") or "").strip()

MONGODB_URI = (os.getenv("MONGODB_URI") or "").strip()
MONGODB_DB_NAME = (os.getenv("MONGODB_DB_NAME") or "healthcare_chatbot").strip()
MONGODB_USERS_COLLECTION = (os.getenv("MONGODB_USERS_COLLECTION") or "login").strip()
MONGODB_CHAT_COLLECTION = (os.getenv("MONGODB_CHAT_COLLECTION") or "chat_history").strip()

MAX_CONTENT_LENGTH = 16 * 1024 * 1024
PERMANENT_SESSION_LIFETIME = timedelta(days=30)
SEND_FILE_MAX_AGE_DEFAULT = 0

EMERGENCY_KEYWORDS = [
    "chest pain",
    "shortness of breath",
    "difficulty breathing",
    "fainting",
    "unconscious",
    "seizure",
    "stroke",
    "severe bleeding",
    "blood in vomit",
    "suicidal",
]

TRACKED_SYMPTOMS = [
    "fever",
    "cough",
    "cold",
    "headache",
    "sore throat",
    "vomiting",
    "diarrhea",
    "fatigue",
    "dizziness",
    "chest pain",
    "stomach pain",
    "body pain",
]

SUPPORTED_LANGUAGES = {"english", "gujarati", "hindi"}
LANGUAGE_ALIASES = {
    "en": "english",
    "en-us": "english",
    "en-in": "english",
    "english": "english",
    "gu": "gujarati",
    "gu-in": "gujarati",
    "gujarati": "gujarati",
    "hi": "hindi",
    "hi-in": "hindi",
    "hindi": "hindi",
}
MOJIBAKE_HINTS = ("\u00c3", "\u00c2", "\u00e2", "\u00e0\u00a4", "\u00e0\u00aa")

LANGUAGE_LABELS = {"hindi": "Hindi", "gujarati": "Gujarati", "english": "English"}

AGE_REQUIRED_MESSAGES = {
    "english": "I need your age to provide personalized advice. Please add it in profile settings.",
    "hindi": "Please add your age in profile settings to get personalized advice. (Hindi mode)",
    "gujarati": "Please add your age in profile settings to get personalized advice. (Gujarati mode)",
}

PERSONALIZED_ADVICE_REQUEST_MESSAGES = {
    "english": "I want my personalized health advice",
    "hindi": "[Hindi] I want my personalized health advice",
    "gujarati": "[Gujarati] I want my personalized health advice",
}

LAB_UPLOAD_MESSAGES = {
    "english": "I've uploaded a laboratory report: {filename}",
    "hindi": "[Hindi] Lab report uploaded: {filename}",
    "gujarati": "[Gujarati] Lab report uploaded: {filename}",
}

CHAT_ERROR_MESSAGES = {
    "english": "Sorry, there is a temporary technical issue. Please try again.",
    "hindi": "??? ?????, ??? ?????? ?????? ??? ????? ?????? ?????? ?????",
    "gujarati": "??? ????, ?????? ??????? ?????? ??. ???? ????? ??? ?????? ???.",
}


def apply_app_config(app):
    if not FLASK_SECRET_KEY:
        raise ValueError("FLASK_SECRET_KEY not found in environment variables")

    app.secret_key = FLASK_SECRET_KEY
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = SEND_FILE_MAX_AGE_DEFAULT
    app.config["PERMANENT_SESSION_LIFETIME"] = PERMANENT_SESSION_LIFETIME


def validate_required_secrets():
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables")


def ensure_directories():
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

