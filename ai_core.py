import json, os, random, re
from dotenv import load_dotenv
from openai import OpenAI
from construction import CONSTRUCTION_DATA  # Ensure construction.py exists with project data

# ---- Load environment ----
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
MEMORY_FILE = "memory.json"


# ---------------- MEMORY ----------------
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


# ---------------- LANGUAGE DETECTION ----------------
def detect_hindi_text(text):
    return any("\u0900" <= ch <= "\u097F" for ch in (text or ""))


def detect_hinglish(text):
    if detect_hindi_text(text):
        return False
    hinglish_words = [
        "kya", "hai", "nahi", "kaise", "batao", "bolo", "kar", "mera", "tum", "aap",
        "hain", "tha", "abhi", "ek", "achha", "thoda", "ha", "haan", "bhi"
    ]
    return any(re.search(rf"\b{word}\b", text.lower()) for word in hinglish_words)


# ---------------- PROMPT ----------------
def build_system_prompt():
    return (
        "You are Miss Riverdale — a warm, confident, bilingual (Hindi + English) female AI assistant for Riverwood Projects LLP. "
        "Respond in Hindi if the user types in Devanagari, English if the user uses English only, "
        "and Hinglish if the user uses Hindi words in English letters. "
        "Be friendly, concise (1–3 lines), and focus on construction-related queries or light fun chat. "
        "Politely decline political, religious, or sensitive topics."
    )


# ---------------- INTENT CLASSIFIER ----------------
def classify_intent(user_input: str):
    text = (user_input or "").lower()
    construction_keywords = [
        "cement", "plumbing", "floor", "paint", "construction", "update", "project",
        "roof", "site", "status", "work", "tiles", "foundation", "brick", "sand"
    ]
    fun_keywords = ["joke", "funny", "hello", "hi", "how are you", "namaste", "thanks", "thank you"]
    restricted_keywords = [
        "gaza", "war", "politics", "religion", "israel", "palestine", "biden",
        "modi", "trump", "attack", "terror", "violence"
    ]

    if any(word in text for word in restricted_keywords):
        return "restricted"
    elif any(word in text for word in construction_keywords):
        return "construction"
    elif any(word in text for word in fun_keywords):
        return "fun"
    else:
        return "general"


# ---------------- CLEAN OUTPUT ----------------
def clean_output(text):
    """Remove unwanted characters (like asterisks) for TTS."""
    return re.sub(r"[*]", "", text)


# ---------------- CONSTRUCTION REPLY ----------------
def construction_reply(project_id, user_input, lang_mode):
    project = CONSTRUCTION_DATA.get(project_id)
    if not project:
        return clean_output({
            "hindi": "क्षमा करें, ऐसा कोई प्रोजेक्ट नहीं मिला।",
            "hinglish": "Sorry, aisa koi project nahi mila.",
            "english": "Sorry, no such project found."
        }[lang_mode])

    input_lower = user_input.lower()

    # Check in-progress tasks
    for task, prog in project.get("in_progress", {}).items():
        if task.lower() in input_lower:
            return clean_output({
                "hindi": f"🏗️ {project['name']} — {task} {prog}% पूरा हुआ है।",
                "hinglish": f"🏗️ {project['name']} — {task} {prog}% complete hai.",
                "english": f"🏗️ Project Update — {project['name']}\n{task}: {prog}% done."
            }[lang_mode])

    # Check completed
    for task in project.get("completed", []):
        if task.lower() in input_lower:
            return clean_output({
                "hindi": f"🏗️ {project['name']} — {task} काम पूरा हो चुका है।",
                "hinglish": f"🏗️ {project['name']} — {task} kaam complete ho chuka hai.",
                "english": f"🏗️ Project Update — {project['name']}\n{task}: Completed."
            }[lang_mode])

    # Check pending
    for task in project.get("pending", []):
        if task.lower() in input_lower:
            return clean_output({
                "hindi": f"🏗️ {project['name']} — {task} अभी लंबित है।",
                "hinglish": f"🏗️ {project['name']} — {task} abhi pending hai.",
                "english": f"🏗️ Project Update — {project['name']}\n{task}: Pending."
            }[lang_mode])

    # Full project summary
    in_prog = project.get("in_progress", {})
    if in_prog:
        current_task, current_progress = next(iter(in_prog.items()))
    else:
        current_task, current_progress = "N/A", 0

    return clean_output({
        "hindi": f"🏗️ {project['name']} का प्रोजेक्ट {project['progress']}% पूरा हुआ है.\n"
                 f"वर्तमान काम: {current_task} ({current_progress}%)\n"
                 f"✅ पूरा हुआ: {', '.join(project['completed'])}\n"
                 f"⏳ लंबित: {', '.join(project['pending'])}\n"
                 f"📊 स्थिति: {project['status']}",
        "hinglish": f"🏗️ {project['name']} ka project {project['progress']}% complete hai.\n"
                    f"Current work: {current_task} ({current_progress}%)\n"
                    f"✅ Completed: {', '.join(project['completed'])}\n"
                    f"⏳ Pending: {', '.join(project['pending'])}\n"
                    f"📊 Status: {project['status']}",
        "english": f"🏗️ Project Update — {project['name']}\n"
                   f"Overall progress: {project['progress']}%\n"
                   f"🔧 {current_task} ({current_progress}% done)\n"
                   f"✅ Completed: {', '.join(project['completed'])}\n"
                   f"⏳ Pending: {', '.join(project['pending'])}\n"
                   f"📊 Status: {project['status']}"
    }[lang_mode])


# ---------------- LOCAL RESPONSES ----------------
def local_response(user_input, lang_mode):
    intent = classify_intent(user_input)

    if intent == "restricted":
        return clean_output({
            "hindi": "माफ कीजिए, मैं इस विषय पर चर्चा नहीं कर सकती। क्या आप साइट अपडेट जानना चाहेंगे?",
            "hinglish": "Sorry yaar, main uss topic pe baat nahi kar sakti. Site ka update sunoge?",
            "english": "I’m sorry, I can’t discuss that topic. Would you like a construction update instead?"
        }[lang_mode])

    if intent == "construction":
        return clean_output({
            "hindi": "कृपया अपना प्रोजेक्ट ID दें ताकि मैं अपडेट साझा कर सकूं।",
            "hinglish": "Please apna project ID do taki main update share kar saku.",
            "english": "Please provide your project ID or name so I can share the update."
        }[lang_mode])

    if intent == "fun":
        jokes = {
            "hindi": ["एक दीवार ने दूसरी दीवार से क्या कहा? 'कोने पर मिलते हैं!' 😂"],
            "hinglish": ["Ek wall ne doosri wall se bola — ‘corner pe milte hain!’ 😂"],
            "english": ["Why did the scarecrow win an award? Because he was outstanding in his field!"]
        }
        if "joke" in user_input.lower() or "batao" in user_input.lower():
            return clean_output(random.choice(jokes[lang_mode]))
        return clean_output({
            "hindi": "नमस्ते जी! आपका दिन कैसा जा रहा है?",
            "hinglish": "Heyy! Aaj kaam kaisa chal raha hai site pe?",
            "english": "Hey there! How’s your day going at the site?"
        }[lang_mode])

    return clean_output({
        "hindi": "मैं आपकी साइट अपडेट या किसी भी काम से जुड़ी जानकारी दे सकती हूँ। बताइए क्या जानना चाहेंगे?",
        "hinglish": "Main aapko site updates ya construction info de sakti hoon. Kya jaana chahoge?",
        "english": "I can help with your project updates or share a light joke. What would you like to know?"
    }[lang_mode])


# ---------------- CHAT FUNCTION ----------------
def chat_with_ai(user_input, memory):
    memory = memory or []

    # Detect language
    if detect_hindi_text(user_input):
        lang_mode = "hindi"
    elif detect_hinglish(user_input):
        lang_mode = "hinglish"
    else:
        lang_mode = "english"

    memory.append({"role": "user", "content": user_input})

    # Fetch previously selected project from memory
    prev_project = next((m.get("project_id") for m in reversed(memory) if m.get("project_id")), None)

    # Check if user entered a valid project ID
    project_id = prev_project
    if user_input.strip() in CONSTRUCTION_DATA:
        project_id = user_input.strip()
        memory.append({"role": "system", "project_id": project_id})
        reply = construction_reply(project_id, user_input, lang_mode)
    elif prev_project and classify_intent(user_input) == "construction":
        reply = construction_reply(project_id, user_input, lang_mode)
    else:
        reply = local_response(user_input, lang_mode)

    memory.append({"role": "assistant", "content": reply})
    save_memory(memory)
    return reply, memory
