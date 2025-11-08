# voice_utils.py — Miss Riverdale: Expressive, Natural Bilingual Voice
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import tempfile, os, uuid, time, re, random
import pygame

# ---------- Initialize offline engine ----------
_engine = pyttsx3.init()
_engine.setProperty("rate", 300)
voices = _engine.getProperty("voices")
if len(voices) > 1:
    _engine.setProperty("voice", voices[1].id)  # female if available
else:
    _engine.setProperty("voice", voices[0].id)


def _is_hindi_text(text: str) -> bool:
    return any("\u0900" <= ch <= "\u097F" for ch in (text or ""))


def _split_phrases(text: str):
    """
    Split text into small, expressive chunks based on punctuation
    """
    # Split while keeping punctuation marks
    chunks = re.split(r'([.?!,;:])', text)
    phrases = []
    current = ""
    for chunk in chunks:
        current += chunk
        if re.match(r'[.?!,;:]$', chunk.strip()):
            phrases.append(current.strip())
            current = ""
    if current.strip():
        phrases.append(current.strip())
    return phrases


def _pause_for_punctuation(punct):
    """Return natural pause length for each punctuation mark"""
    return {
        '.': random.uniform(0.5, 0.8),
        ',': random.uniform(0.25, 0.4),
        ';': random.uniform(0.3, 0.5),
        ':': random.uniform(0.3, 0.5),
        '?': random.uniform(0.6, 0.9),
        '!': random.uniform(0.5, 0.7),
        '*': random.uniform(0.5, 0.7),
        '**': random.uniform(0.5, 0.7)
    }.get(punct, random.uniform(0.3, 0.6))


def speak(text: str):
    """
    Speak text with natural pacing and emotion.
    - Slows down politely for greetings
    - Adds pauses for punctuation
    - Slight tone variation for realism
    """
    text = text.strip()
    if not text:
        return

    lang = "hi" if _is_hindi_text(text) else "en"
    phrases = _split_phrases(text)

    # emotional rate adjustment
    if any(g in text.lower() for g in ["namaste", "hello", "good morning", "hi"]):
        speech_rate = 0.95
    elif any(q in text for q in ["?", "why", "how", "kya", "kyon"]):
        speech_rate = 1.05
    else:
        speech_rate = 1.0

    try:
        for phrase in phrases:
            phrase = phrase.strip()
            if not phrase:
                continue

            filename = os.path.join(tempfile.gettempdir(), f"riverdale_{uuid.uuid4().hex}.mp3")
            tts = gTTS(text=phrase, lang=lang, slow=False)
            tts.save(filename)

            pygame.mixer.init()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.set_volume(random.uniform(0.87, 1.0))
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                time.sleep(0.1 * speech_rate)

            pygame.mixer.music.unload()
            pygame.mixer.quit()
            if os.path.exists(filename):
                os.remove(filename)

            # pause depending on punctuation
            last_char = phrase[-1] if phrase else ""
            time.sleep(_pause_for_punctuation(last_char))

    except Exception as e:
        print(f"⚠️ gTTS failed ({e}) — switching to offline voice.")
        try:
            for phrase in phrases:
                _engine.say(phrase)
                _engine.runAndWait()
                time.sleep(_pause_for_punctuation(phrase[-1] if phrase else "."))
        except Exception as e:
            print("⚠️ pyttsx3 error:", e)


def listen(language_mode="auto"):
    """
    Listen and transcribe speech using Google STT.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening…")
        r.adjust_for_ambient_noise(source, duration=0.5)
        audio = r.listen(source, phrase_time_limit=8)
    try:
        if language_mode == "en":
            return r.recognize_google(audio, language="en-IN")
        elif language_mode == "hi":
            return r.recognize_google(audio, language="hi-IN")
        else:
            try:
                return r.recognize_google(audio, language="en-IN")
            except Exception:
                return r.recognize_google(audio, language="hi-IN")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print("⚠️ STT error:", e)
        return ""
