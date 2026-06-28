# Healthcare Chatbot: Interview & Viva Guide

## 1) One-line Project Summary
A multilingual AI healthcare assistant built with Flask + Groq that supports symptom-based guidance, lab report explanation, personalized health advice, audio transcription, and user-level conversation analytics.

## 2) Core Problem It Solves
- Makes basic healthcare guidance more accessible in English, Gujarati, and Hindi.
- Helps users understand lab reports in simple language.
- Keeps user-specific chat history and shows insights on a dashboard.

## 3) Key Features
- User authentication (signup/login/logout).
- Language selection (English/Gujarati/Hindi).
- Symptom chat assistant (LLM-powered, no medicine recommendations).
- Lab report upload and analysis (`.pdf`, `.doc/.docx`, `.txt`, `.csv`).
- Personalized health advice using profile fields (age + gender).
- Voice input transcription using Groq Whisper.
- Dashboard with:
  - conversation history,
  - symptom trends,
  - emergency keyword signal counts,
  - recommendations.

## 4) Tech Stack
- Backend: Python, Flask
- AI: Groq API (`llama-3.3-70b-versatile`, `whisper-large-v3-turbo`)
- Storage: MongoDB (primary when configured), JSON files fallback
- Frontend: Jinja templates + HTML/CSS + vanilla JS
- Libraries: `flask`, `groq`, `werkzeug`, `PyPDF2`, `python-docx`, `pymongo`, `python-dotenv`, `waitress`

## 5) Architecture (High Level)
1. User authenticates.
2. Session stores user identity + language + profile.
3. User sends chat/report/audio.
4. Backend calls Groq models.
5. Message + metadata are saved in storage.
6. Dashboard reads chat records and computes analytics.

Main code file: `app.py`
Templates: `templates/*.html`
Styles: `static/*.css`
Data fallback: `data/users.json`, `data/chat_history.json`

## 6) Storage Strategy (Important)
- App tries MongoDB first.
- If MongoDB URI is missing/placeholder/unreachable, it automatically uses local JSON files.
- On first successful Mongo connection, legacy JSON data can be migrated into Mongo collections.

Configured env keys:
- `FLASK_SECRET_KEY`
- `GROQ_API_KEY`
- `MONGODB_URI`
- `MONGODB_DB_NAME`
- `MONGODB_USERS_COLLECTION`
- `MONGODB_CHAT_COLLECTION`

## 7) Major API Routes
Public:
- `GET /` -> redirects to auth
- `GET /auth` -> login/signup page
- `POST /set_site_language` -> sets site language before auth
- `GET /api/health/db` -> storage health
- `GET /api/health/full` -> health + metrics
- `POST /signup`
- `POST /login`

Protected (login required):
- `GET /experience` -> 3D onboarding page
- `GET /chat`
- `POST /send_message`
- `POST /transcribe_audio`
- `POST /upload_report`
- `POST /get_personalized_advice`
- `POST /set_language` (language + gender + age)
- `POST /new_conversation`
- `POST /clear_chat`
- `GET /dashboard`
- `GET /dashboard/export`
- `GET /logout`

## 8) AI Prompt Safety Choices
The system prompts enforce:
- only health-related responses,
- language-specific output,
- structured sections,
- no medicine recommendations,
- no direct diagnosis style output.

## 9) Dashboard Analytics Logic
Calculated from user chat history:
- total/user/assistant message counts,
- total conversations,
- lab report message count,
- personalized advice count,
- emergency keyword mentions,
- top symptom frequency from tracked symptoms list,
- recommendations based on missing usage patterns.

## 10) Why This Project Is Not Just a Basic Chatbot
- Multilingual UX across auth/chat/dashboard.
- Profile-aware prompting (age/gender context).
- Report parsing for multiple file formats.
- Audio transcription pipeline.
- Analytics dashboard with conversation-level insights.
- Pluggable storage backend (Mongo + JSON fallback).

## 11) Common Questions and Strong Answers

### Q1: Why Flask?
Flask keeps routing, session handling, and template rendering simple, so we could focus on healthcare flow and AI integration without framework overhead.

### Q2: How is user data separated?
Each chat record stores `user_id`, `session_id`, and `conversation_id`, and dashboard queries filter by current logged-in `user_id`.

### Q3: How do you support multilingual behavior?
Language is normalized and stored in session, then used for UI labels plus model prompts so both frontend and AI output stay in the selected language.

### Q4: How do you prevent unsafe medical advice?
System prompts explicitly block medicine recommendations and enforce guidance-style responses (symptoms/causes/care/doctor escalation).

### Q5: What happens if MongoDB is down?
The app degrades to JSON-based local storage automatically so core functionality still works.

### Q6: How do you process lab reports?
Uploaded files are sanitized with `secure_filename`, parsed by file-type readers, then content is sent to an LLM prompt focused on deficiencies and dietary/lifestyle suggestions.

### Q7: How is authentication handled?
Users sign up/login using hashed passwords (`werkzeug` hash). Session tracks login state. Unauthorized API access is blocked in `before_request`.

### Q8: How does voice input work?
Frontend records audio, sends it to `/transcribe_audio`, backend calls Groq Whisper model, and transcript text is returned for chat submission.

### Q9: What are the key limitations?
No clinical validation layer, no role-based admin, no formal automated test suite, and no production hardening like CSRF/rate-limiting yet.

### Q10: What would you improve next?
Add test coverage, structured medical guardrails, stronger security controls, async/background processing for heavy files, and production deployment config.

## 12) Security and Reliability Notes (Be Honest in Viva)
Current strengths:
- Password hashing
- Session-based auth gates
- File extension whitelist
- Input validation for age/gender/language

Current gaps:
- No CSRF protection
- No rate limiting
- No explicit XSS sanitization layer for rendered message HTML
- Local JSON data is not ideal for production scale/privacy

## 13) How to Run (Quick)
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Set `.env` values (secret key, Groq key, Mongo values).
3. Start app:
   - `python app.py`
4. Open:
   - `http://127.0.0.1:5001/auth`

## 14) 30-Second Pitch (Memorize)
"This is a Flask-based multilingual healthcare assistant that uses Groq LLM models for symptom guidance, lab report interpretation, and personalized preventive advice. It supports text plus voice input, stores user conversations with session metadata, and visualizes insights like symptom trends and emergency mentions on a dashboard. It is designed with a practical fallback architecture: MongoDB in production and JSON locally, so the app remains usable even if external storage is unavailable."

## 15) If Someone Asks: "Is it a real diagnostic system?"
Best answer:
"No. It is a guidance and educational assistant, not a diagnostic replacement for a licensed doctor. The prompts are intentionally constrained to avoid medicine recommendations and direct diagnosis claims."
