# Healthcare Chatbot Architecture

## Layers
- `src/healthcare_chatbot/core`: app factory, env config, lifecycle hooks
- `src/healthcare_chatbot/api/routes`: HTTP endpoints grouped by domain
- `src/healthcare_chatbot/services`: AI and report-processing business logic
- `src/healthcare_chatbot/repositories`: persistence adapters (Mongo + JSON fallback)
- `src/healthcare_chatbot/utils`: cross-cutting helpers

## Entry Points
- `app.py`: local runtime entry
- `wsgi.py`: production WSGI entrypoint
- `asgi.py`: ASGI-compatible entrypoint
