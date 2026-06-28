from flask import jsonify, redirect, render_template, session

from healthcare_chatbot.core.config import EMERGENCY_KEYWORDS, TRACKED_SYMPTOMS
from healthcare_chatbot.utils.helpers import is_logged_in, keyword_count, normalize_language
from healthcare_chatbot.repositories import storage


def register_dashboard_routes(app):
    @app.route("/dashboard", methods=["GET"])
    def dashboard():
        if not is_logged_in():
            return redirect("/auth")
        session["has_seen_dashboard"] = True
        session.modified = True
        current_user = session.get("user_id")
        records = storage.get_user_chat_records(current_user)
        records.sort(key=lambda row: row.get("created_at", ""))

        conversations_map = {}
        for row in records:
            cid = row.get("conversation_id", "unknown")
            conversations_map.setdefault(cid, []).append(row)

        conversations = []
        for cid, rows in conversations_map.items():
            rows.sort(key=lambda item: item.get("created_at", ""))
            first = rows[0]
            last = rows[-1]
            conversations.append({
                "conversation_id": cid,
                "start_time": first.get("created_at", ""),
                "end_time": last.get("created_at", ""),
                "language": first.get("language") or "unknown",
                "message_count": len(rows),
                "preview": (last.get("content_text") or "")[:120],
            })
        conversations.sort(key=lambda conv: conv["end_time"], reverse=True)

        user_messages = [row for row in records if row.get("role") == "user"]
        assistant_messages = [row for row in records if row.get("role") == "assistant"]

        emergency_mentions = 0
        symptom_counter = {symptom: 0 for symptom in TRACKED_SYMPTOMS}
        for row in user_messages:
            text = (row.get("content_text") or "").lower()
            emergency_mentions += keyword_count(text, EMERGENCY_KEYWORDS)
            for symptom in TRACKED_SYMPTOMS:
                if symptom in text:
                    symptom_counter[symptom] += 1

        top_symptoms = [
            {"name": key, "count": value}
            for key, value in sorted(symptom_counter.items(), key=lambda item: item[1], reverse=True)
            if value > 0
        ][:8]

        stats = {
            "total_messages": len(records),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "total_conversations": len(conversations),
            "lab_reports": sum(1 for row in records if row.get("message_type") == "lab_report"),
            "personalized_advice": sum(1 for row in records if row.get("message_type") == "personalized_advice"),
            "emergency_mentions": emergency_mentions,
        }

        recommendations = []
        language = normalize_language(session.get("language"), "english")
        recommendation_text = {
            "english": {
                "emergency": "Potential emergency keywords detected. Use local emergency services for severe symptoms.",
                "lab": "Upload at least one lab report to get nutrition and deficiency-focused suggestions.",
                "advice": "Use Personalized Advice at least once to get age and gender-specific preventive guidance.",
                "symptoms": "Share symptom details in plain language to improve the quality of healthcare responses.",
                "complete": "Your history looks complete. Continue tracking symptom changes and duration for better follow-up.",
            },
            "gujarati": {
                "emergency": "Emergency-type symptoms found. Please use local emergency services for severe symptoms.",
                "lab": "Upload at least one lab report for better nutrition and deficiency suggestions.",
                "advice": "Use Personalized Advice at least once for age and gender-specific guidance.",
                "symptoms": "Share symptom details clearly for better responses.",
                "complete": "Your history looks good. Keep tracking symptom changes and duration.",
            },
            "hindi": {
                "emergency": "Emergency-type signals detected. For severe symptoms, contact local emergency services.",
                "lab": "Upload at least one lab report for deficiency and nutrition-focused recommendations.",
                "advice": "Use Personalized Advice at least once for age and gender-based prevention guidance.",
                "symptoms": "Describe symptoms clearly to improve response quality.",
                "complete": "Your history looks complete. Continue tracking symptoms and duration.",
            },
        }.get(language, {})
        if stats["emergency_mentions"] > 0:
            recommendations.append(recommendation_text.get("emergency", "Potential emergency keywords detected. Use local emergency services for severe symptoms."))
        if stats["lab_reports"] == 0:
            recommendations.append(recommendation_text.get("lab", "Upload at least one lab report to get nutrition and deficiency-focused suggestions."))
        if stats["personalized_advice"] == 0:
            recommendations.append(recommendation_text.get("advice", "Use Personalized Advice at least once to get age and gender-specific preventive guidance."))
        if not top_symptoms:
            recommendations.append(recommendation_text.get("symptoms", "Share symptom details in plain language to improve the quality of healthcare responses."))
        if not recommendations:
            recommendations.append(recommendation_text.get("complete", "Your history looks complete. Continue tracking symptom changes and duration for better follow-up."))

        return render_template(
            "dashboard.html",
            user_name=session.get("user_name"),
            stats=stats,
            conversations=conversations,
            records=list(reversed(records[-200:])),
            top_symptoms=top_symptoms,
            recommendations=recommendations,
            language=language,
        )

    @app.route("/dashboard/export", methods=["GET"])
    def export_dashboard_data():
        current_user = session.get("user_id")
        records = storage.get_user_chat_records(current_user)
        return jsonify({"records": records, "count": len(records)})

