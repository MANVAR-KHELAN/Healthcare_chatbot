import os

from flask import jsonify, redirect, render_template, request, session

from healthcare_chatbot.core.config import (
    AGE_REQUIRED_MESSAGES,
    CHAT_ERROR_MESSAGES,
    LAB_UPLOAD_MESSAGES,
    PERSONALIZED_ADVICE_REQUEST_MESSAGES,
    SUPPORTED_LANGUAGES,
)
from healthcare_chatbot.utils.helpers import (
    is_logged_in,
    language_text,
    log_message,
    normalize_language,
    start_new_conversation,
    validate_age,
)
from healthcare_chatbot.services.ai_service import (
    get_disease_prediction,
    get_personalized_health_advice,
)
from healthcare_chatbot.services.report_service import process_lab_report
import healthcare_chatbot.services.ai_service as services
from healthcare_chatbot.repositories import storage
from werkzeug.utils import secure_filename


def register_chat_routes(app):
    @app.route("/chat", methods=["GET"])
    def home():
        if not is_logged_in():
            return redirect("/auth")
        conversation_id = (request.args.get("conversation_id") or "").strip()
        if conversation_id:
            current_user = session.get("user_id")
            user_records = storage.get_user_chat_records(current_user)
            selected = [
                row for row in user_records if row.get("conversation_id") == conversation_id
            ]
            if selected:
                selected.sort(key=lambda row: row.get("created_at", ""))
                session["conversation_id"] = conversation_id
                session["messages"] = [
                    {
                        "role": row.get("role"),
                        "content": row.get("content"),
                        "created_at": row.get("created_at"),
                        "message_type": row.get("message_type", "chat"),
                    }
                    for row in selected
                ]
                session.modified = True
        if not session.get("has_seen_dashboard"):
            session["has_seen_dashboard"] = True
            session.modified = True
        return render_template(
            "chat.html",
            messages=session["messages"],
            language=session.get("language"),
            gender=session.get("gender"),
            age=session.get("age"),
        )

    @app.route("/set_language", methods=["POST"])
    def set_language():
        data = request.json or {}
        language = normalize_language(data.get("language"))
        gender = data.get("gender")
        age = data.get("age")

        if language not in SUPPORTED_LANGUAGES:
            return jsonify({"success": False, "error": "Invalid language selection"}), 400

        if gender not in ["male", "female", "other"]:
            return jsonify({"success": False, "error": "Please select your gender"}), 400

        age_val = validate_age(age)
        if age_val is None:
            return jsonify({"success": False, "error": "Please enter a valid age (1-120)"}), 400

        session["language"] = language
        session["gender"] = gender
        session["age"] = age_val
        session.permanent = True
        start_new_conversation()

        return jsonify({"success": True, "language": language})

    @app.route("/clear_chat", methods=["POST"])
    def clear_chat():
        start_new_conversation()
        session["gender"] = None
        session["age"] = None
        session.modified = True
        return jsonify({"success": True})

    @app.route("/new_conversation", methods=["POST"])
    def new_conversation():
        if not is_logged_in():
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        start_new_conversation()
        return jsonify({"success": True})

    @app.route("/send_message", methods=["POST"])
    def send_message():
        data = request.get_json(silent=True) or {}
        user_input = (data.get("user_input") or "").strip()

        if not user_input:
            return jsonify({"error": "No user input provided"}), 400

        language = normalize_language(session.get("language"), "english")

        try:
            response = get_disease_prediction(user_input, language)
            log_message("user", user_input, "chat")
            log_message("assistant", response, "chat")
            return jsonify({"response": response})
        except Exception as exc:
            print(f"[send_message] error: {exc}")
            return jsonify({"error": language_text(language, CHAT_ERROR_MESSAGES)}), 500

    @app.route("/transcribe_audio", methods=["POST"])
    def transcribe_audio():
        if "audio_file" not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"}), 400

        audio_file = request.files.get("audio_file")
        if audio_file is None or audio_file.filename == "":
            return jsonify({"success": False, "error": "No audio file selected"}), 400

        audio_bytes = audio_file.read()
        if not audio_bytes:
            return jsonify({"success": False, "error": "Audio file is empty"}), 400

        language = normalize_language(
            request.form.get("language") or session.get("language"), "english"
        )
        whisper_language = {
            "english": "en",
            "hindi": "hi",
            "gujarati": "gu",
        }.get(language, "en")

        if services.client is None or not hasattr(services.client, "audio"):
            return jsonify({
                "success": False,
                "error": "Audio transcription is temporarily unavailable. Please type your message.",
            }), 503

        try:
            transcript_resp = services.client.audio.transcriptions.create(
                file=(audio_file.filename or "voice-input.webm", audio_bytes),
                model="whisper-large-v3-turbo",
                language=whisper_language,
                response_format="json",
            )
        except Exception:
            try:
                transcript_resp = services.client.audio.transcriptions.create(
                    file=(audio_file.filename or "voice-input.webm", audio_bytes),
                    model="whisper-large-v3-turbo",
                    response_format="json",
                )
            except Exception as exc:
                print(f"[transcribe_audio] error: {exc}")
                return jsonify({"success": False, "error": "Audio transcription is temporarily unavailable. Please type your message."}), 503

        transcript = ""
        if isinstance(transcript_resp, dict):
            transcript = (transcript_resp.get("text") or "").strip()
        else:
            transcript = (getattr(transcript_resp, "text", "") or "").strip()

        if not transcript:
            return jsonify({"success": False, "error": "Could not transcribe the audio"}), 422

        return jsonify({"success": True, "transcript": transcript})

    @app.route("/upload_report", methods=["POST"])
    def upload_report():
        if "report_file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["report_file"]
        if not file.filename:
            return jsonify({"error": "No selected file"}), 400

        allowed_extensions = {".pdf", ".doc", ".docx", ".txt", ".csv"}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({"error": "Unsupported file format. Please upload PDF, DOC, DOCX, TXT, or CSV files."}), 400

        file_path = ""
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            language = normalize_language(session.get("language"), "english")
            response = process_lab_report(file_path, language)

            user_message = language_text(language, LAB_UPLOAD_MESSAGES).format(filename=filename)
            log_message("user", user_message, "lab_report")
            log_message("assistant", response, "lab_report")

            os.remove(file_path)
            return jsonify({"success": True, "filename": filename, "response": response})
        except Exception as e:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500

    @app.route("/get_personalized_advice", methods=["POST"])
    def get_personalized_advice_route():
        language = normalize_language(session.get("language"), "english")

        if not session.get("age"):
            return jsonify({
                "response": language_text(language, AGE_REQUIRED_MESSAGES),
                "type": "personalized_advice",
            })

        try:
            advice = get_personalized_health_advice(language)
            user_message = language_text(language, PERSONALIZED_ADVICE_REQUEST_MESSAGES)

            log_message("user", user_message, "personalized_advice")
            log_message("assistant", advice, "personalized_advice")

            return jsonify({"response": advice, "type": "personalized_advice"})
        except Exception as e:
            return jsonify({"error": f"Error getting personalized advice: {str(e)}"}), 500



