import json, random, os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
MEMORY_FILE = "memory.json"


def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            f.write("[]")
        return []


def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("⚠️ Error saving memory:", e)


def detect_hindi_text(text):
    return any("\u0900" <= ch <= "\u097F" for ch in (text or ""))


def build_system_prompt():
    return (
        "You are Miss Riverdale — a bilingual, warm, confident, female AI assistant for Riverwood Projects LLP. "
        "Respond in Hindi if the user uses Devanagari text, English otherwise, or a Hinglish blend if needed. "
        "Be professional yet friendly, concise (1–3 sentences), and emotionally natural."
    )


def fallback_reply(user_input, prefers_hindi):
    text = (user_input or "").lower()
    if "update" in text or "site" in text:
        return "Namaste ji! Aaj ka update — Tower A painting ka kaam shuru hua hai." if prefers_hindi else "Today's update — painting work has started at Tower A."
    if "hello" in text or "namaste" in text:
        return "Namaste ji! Kaise hain aap?" if prefers_hindi else "Hey there! How are you doing today?"
    return "Main yahan hoon aapki madad ke liye." if prefers_hindi else "I'm here to help you with anything related to your project."


def chat_with_ai(user_input, memory):
    memory = memory or []
    prefers_hindi = detect_hindi_text(user_input)
    memory.append({"role": "user", "content": user_input})

    if not client:
        reply = fallback_reply(user_input, prefers_hindi)
    else:
        try:
            messages = [
                {"role": "system", "content": build_system_prompt()},
                {"role": "system", "content": "User language: Hindi." if prefers_hindi else "User language: English."},
            ] + [{"role": m["role"], "content": m["content"]} for m in memory[-6:]] + [
                {"role": "user", "content": user_input}
            ]

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=250,
                temperature=0.8,
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            print("⚠️ OpenAI error:", e)
            reply = fallback_reply(user_input, prefers_hindi)

    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)
    return reply, memory
