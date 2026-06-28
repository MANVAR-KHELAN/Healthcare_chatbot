from flask import session
from groq import Groq

from healthcare_chatbot.core.config import GROQ_API_KEY, LANGUAGE_LABELS, AGE_REQUIRED_MESSAGES
from healthcare_chatbot.utils.helpers import normalize_language, repair_mojibake, format_response, language_text

client = None
ai_unavailable_reason = ""


FALLBACK_CHAT_RESPONSES = {
    "english": """## Symptoms
From what you shared, this may be a common health issue, but I cannot confirm a diagnosis.

## Possible Causes
Could be related to infection, inflammation, stress, dehydration, or lifestyle factors.

## Care
- Rest and hydrate well
- Eat light and balanced meals
- Track symptoms (onset, severity, triggers)
- Avoid self-medicating without medical advice

## When to see a doctor
- Symptoms become severe or persistent
- Breathing difficulty, chest pain, confusion, fainting, or high fever
- Any symptom that feels unusual or rapidly worsening""",
    "hindi": """## Symptoms
Aapke lakshan aam health issue se jude ho sakte hain, lekin diagnosis confirm nahi kiya ja sakta.

## Possible Causes
Infection, inflammation, stress, dehydration, ya lifestyle factors ho sakte hain.

## Care
- Aaraam karein aur paani piyen
- Halka aur balanced khana lein
- Lakshan ka record rakhein (kab shuru hua, kitna tez hai)
- Bina doctor ki salah ke dawa na lein

## When to see a doctor
- Lakshan tez ho rahe hon ya lamba samay rahein
- Saans mein dikkat, chest pain, behoshi, confusion, ya high fever""",
    "gujarati": """## Symptoms
Tamara lakshano samanya health issue sathe sambandhit hoi shake chhe, pan diagnosis confirm kari shakay nahi.

## Possible Causes
Infection, inflammation, stress, dehydration, ke lifestyle factors hoi shake.

## Care
- Aram karo ane pani purtu pivo
- Halka ane balanced aahar lo
- Lakshano no record rakho (sharu kyare thayu, ketla gambhir chhe)
- Doctor ni salah vagar dawa na lo

## When to see a doctor
- Lakshano vadhta hoy ke lamba samay sudhi rahe
- Saans ma taklif, chest pain, behoshi, confusion, ke uncho tav""",
}

FALLBACK_LAB_RESPONSES = {
    "english": """## Findings
I could not run full AI analysis right now, but your report text was received.

## Normal Range vs Current Value
Please compare each test value against the reference range shown in your report.
Mark items as low, high, or normal.

## Dietary Suggestions
- Low hemoglobin/iron: leafy greens, lentils, beans, iron-rich foods
- Low B12: dairy, eggs, fortified foods
- Low vitamin D: sunlight exposure and vitamin D rich foods
- High sugar markers: reduce refined sugar, increase fiber

## Lifestyle Changes
- Regular physical activity
- Good hydration and sleep
- Repeat tests and consult a qualified clinician for interpretation""",
    "hindi": """## Findings
Abhi full AI analysis available nahi hai, lekin report text receive ho gaya hai.

## Normal Range vs Current Value
Har test value ko report me diye gaye reference range se compare karein.
Low, high, ya normal mark karein.

## Dietary Suggestions
- Low iron/hemoglobin: leafy greens, lentils, beans
- Low B12: dairy, eggs, fortified foods
- Low vitamin D: dhoop aur vitamin D rich foods
- High sugar markers: refined sugar kam karein, fiber badhayein

## Lifestyle Changes
- Regular exercise
- Paani aur neend ka dhyan rakhein
- Doctor se proper interpretation ke liye consult karein""",
    "gujarati": """## Findings
Haal ma full AI analysis upalabdh nathi, pan report text mali gayu chhe.

## Normal Range vs Current Value
Pratyek test value ne report ma aapel reference range sathe compare karo.
Low, high ke normal tarike mark karo.

## Dietary Suggestions
- Low iron/hemoglobin: leafy greens, lentils, beans
- Low B12: dairy, eggs, fortified foods
- Low vitamin D: suryaprakaash ane vitamin D rich foods
- High sugar markers: refined sugar ochhu karo, fiber vadharo

## Lifestyle Changes
- Niyamit vyayam
- Purti ungh ane hydration
- Proper interpretation mate doctor ni salah lo""",
}


def init_ai_client():
    global client, ai_unavailable_reason
    if not GROQ_API_KEY:
        ai_unavailable_reason = "GROQ_API_KEY not found in environment variables"
        client = None
        print(f"[ai_service] {ai_unavailable_reason}. Falling back to local responses.")
        return False
    try:
        client = Groq(api_key=GROQ_API_KEY)
        ai_unavailable_reason = ""
        return True
    except Exception as exc:
        ai_unavailable_reason = str(exc)
        client = None
        print(f"[ai_service] Failed to initialize AI client: {exc}. Falling back to local responses.")
        return False


def user_context_for_prompt():
    parts = []
    gender = session.get("gender")
    age = session.get("age")
    if gender:
        parts.append(f"Gender: {gender}")
    if age:
        parts.append(f"Age: {age} years")
    if not parts:
        return ""
    return "User profile: " + ", ".join(parts) + ".\n\n"


def _fallback_chat_response(language):
    return FALLBACK_CHAT_RESPONSES.get(language, FALLBACK_CHAT_RESPONSES["english"])


def _fallback_lab_response(language):
    return FALLBACK_LAB_RESPONSES.get(language, FALLBACK_LAB_RESPONSES["english"])


def _fallback_personalized_response(language, gender, age):
    profile = f"Age: {age} years, Gender: {gender or 'not specified'}"
    if language == "hindi":
        return (
            "## Key health tips\n"
            f"- Profile: {profile}\n"
            "- Rozana halka exercise aur hydration rakhein\n"
            "- Processed food, excess sugar aur smoking se bachein\n\n"
            "## Prevention\n"
            "- Blood pressure, blood sugar, lipid profile ka regular check karte rahein\n"
            "- Vaccination aur annual preventive check-up ka dhyan rakhein\n\n"
            "## Lifestyle\n"
            "- 7-8 ghante ki neend\n"
            "- Stress management (walk, breathing, meditation)\n\n"
            "## Recommended screenings\n"
            "- Age-based screening doctor ki salah se follow karein\n\n"
            "## Warning signs\n"
            "- Chest pain, breathing difficulty, sudden weakness, severe dehydration par turant care lein"
        )
    if language == "gujarati":
        return (
            "## Key health tips\n"
            f"- Profile: {profile}\n"
            "- Darroj halko vyayam ane hydration jaldavvo\n"
            "- Processed food, vadhu sugar ane smoking thi door raho\n\n"
            "## Prevention\n"
            "- Blood pressure, blood sugar, lipid profile ni niyamit tapaas karavo\n"
            "- Vaccination ane varshik preventive check-up par dhyan aapo\n\n"
            "## Lifestyle\n"
            "- 7-8 kalak ni ungh\n"
            "- Stress management (walk, breathing, meditation)\n\n"
            "## Recommended screenings\n"
            "- Umar anusaar doctor ni salah pramane screening follow karo\n\n"
            "## Warning signs\n"
            "- Chest pain, saans ma taklif, achanak kamjori, severe dehydration hoy to turant care lo"
        )
    return (
        "## Key health tips\n"
        f"- Profile: {profile}\n"
        "- Keep regular hydration, balanced meals, and daily movement\n"
        "- Limit processed food, tobacco, and excess sugar\n\n"
        "## Prevention\n"
        "- Track blood pressure, blood sugar, and lipid profile regularly\n"
        "- Keep vaccinations and annual preventive checks up to date\n\n"
        "## Lifestyle\n"
        "- Aim for 7-8 hours of sleep\n"
        "- Manage stress with walking, breathing, or mindfulness\n\n"
        "## Recommended screenings\n"
        "- Follow age-based screening with your clinician\n\n"
        "## Warning signs\n"
        "- Seek urgent care for chest pain, breathing trouble, fainting, or sudden severe symptoms"
    )


def _create_chat_completion(messages):
    if client is None:
        raise RuntimeError(ai_unavailable_reason or "AI client is not initialized")
    return client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
    )


def get_disease_prediction(symptoms, language="english", is_lab_report=False):
    language = normalize_language(language, "english")
    symptoms = repair_mojibake(symptoms or "")
    messages = session.get("messages", [])
    model_messages = [
        {"role": msg.get("role"), "content": msg.get("content")}
        for msg in messages
        if msg.get("role") in {"user", "assistant"} and msg.get("content")
    ]
    prompt_prefix = user_context_for_prompt()

    if language == "english":
        system_prompt = (
            """You are a healthcare assistant specialized in laboratory report analysis.
Respond in English.
Explain deficiencies with clear sections: findings, normal range vs current value,
dietary suggestions, and lifestyle changes.
Do not provide medicine recommendations or diagnoses."""
            if is_lab_report
            else
            """You are a healthcare assistant.
Respond only to health-related queries in English.
Use clear sections (Symptoms, Causes, Care, When to see a doctor).
Do not provide medicine recommendations or diagnoses.
If unrelated to health, politely decline."""
        )
    else:
        language_label = LANGUAGE_LABELS.get(language, "English")
        if is_lab_report:
            system_prompt = (
                "You are a healthcare assistant for lab-report analysis. "
                f"Reply strictly in {language_label}. Explain findings, possible deficiencies, "
                "normal vs current values, food guidance, and lifestyle tips. "
                "Do not recommend medicines."
            )
        else:
            system_prompt = (
                "You are a healthcare assistant. "
                f"Reply strictly in {language_label}. "
                "Use sections: Symptoms, Causes, Care, and When to see a doctor. "
                "Do not recommend medicines."
            )

    system_prompt = repair_mojibake(prompt_prefix + system_prompt)
    try:
        chat_completion = _create_chat_completion(
            [{"role": "system", "content": system_prompt}] + model_messages + [
                {"role": "user", "content": symptoms}
            ]
        )
        response = chat_completion.choices[0].message.content
    except Exception as exc:
        print(f"[ai_service] get_disease_prediction fallback: {exc}")
        response = _fallback_lab_response(language) if is_lab_report else _fallback_chat_response(language)

    formatted_response = format_response(response, language)
    return repair_mojibake(formatted_response)


def get_personalized_health_advice(language="english"):
    language = normalize_language(language, "english")
    gender = session.get("gender")
    age = session.get("age")

    if not age:
        return language_text(language, AGE_REQUIRED_MESSAGES)

    profile_info = f"Gender: {gender}, Age: {age} years"

    if language == "english":
        system_prompt = f"""You are an experienced healthcare advisor.
User profile: {profile_info}
Provide practical personalized advice in sections:
1) Key health tips
2) Prevention
3) Lifestyle
4) Recommended screenings
5) Warning signs
Do not recommend medicines."""
    else:
        language_label = LANGUAGE_LABELS.get(language, "English")
        system_prompt = f"""You are an experienced health advisor.
User profile: {profile_info}
Reply in {language_label} only with practical, sectioned advice:
1) Key tips
2) Prevention
3) Lifestyle
4) Recommended screenings
5) Warning signs
Do not recommend medicines."""

    system_prompt = repair_mojibake(system_prompt)
    try:
        chat_completion = _create_chat_completion(
            [{"role": "system", "content": system_prompt}]
        )
        response = chat_completion.choices[0].message.content
    except Exception as exc:
        print(f"[ai_service] get_personalized_health_advice fallback: {exc}")
        response = _fallback_personalized_response(language, gender, age)

    return repair_mojibake(format_response(response, language))
