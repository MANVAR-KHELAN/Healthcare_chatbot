# Healthcare Chatbot

Production-ready, multilingual healthcare chatbot built with Flask and Groq.

## Architecture

- `src/healthcare_chatbot/core`: app factory, configuration, lifecycle hooks
- `src/healthcare_chatbot/api/routes`: HTTP routes by domain (auth, chat, dashboard, health)
- `src/healthcare_chatbot/services`: AI and report-processing business logic
- `src/healthcare_chatbot/repositories`: storage adapters (MongoDB + JSON fallback)
- `src/healthcare_chatbot/utils`: shared helpers
- `tests`: unit and integration tests
- `config`: environment config overlays

## Runtime Entry Points

- `app.py`: local development runner
- `wsgi.py`: WSGI production entrypoint
- `asgi.py`: ASGI entrypoint

## Quick Start

1. Copy `.env.example` to `.env` and fill secrets.
2. Install dependencies from `requirements.txt`.
3. Run `python app.py`.

