import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import threading, os, time
import speech_recognition as sr
from ai_core import chat_with_ai, load_memory, OPENAI_API_KEY
from voice_utils import speak
from openai import OpenAI

# ---- THEME COLORS ----
BG = "#F9F9F6"
PRIMARY = "#103C3F"
ACCENT = "#C5A35C"


class RiverdaleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Miss Riverdale | Riverwood Projects LLP")
        self.root.geometry("720x560")
        self.root.config(bg=BG)
        self.root.resizable(False, False)

        self.memory = load_memory()
        self.online_status = tk.StringVar(value="Checking...")
        self._recording = False
        self.record_seconds = 0

        # ----- HEADER -----
        header = tk.Frame(root, bg=PRIMARY, height=80)
        header.pack(fill=tk.X)

        if os.path.exists("396x114.png"):
            try:
                logo = Image.open("396x114.png").resize((120, 35), Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(logo)
                tk.Label(header, image=self.logo, bg=PRIMARY).pack(side=tk.LEFT, padx=12, pady=16)
            except Exception as e:
                print("⚠️ Logo load error:", e)

        tk.Label(header, text="Miss Riverdale", bg=PRIMARY, fg="white",
                 font=("Segoe UI Semibold", 22)).pack(side=tk.LEFT, padx=8, pady=15)

        self.status_label = tk.Label(header, textvariable=self.online_status,
                                     bg=PRIMARY, fg="lightgray",
                                     font=("Segoe UI", 9, "italic"))
        self.status_label.pack(side=tk.RIGHT, padx=14)

        # ----- CHAT AREA -----
        self.chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD,
                                                  width=82, height=20,
                                                  font=("Segoe UI", 11),
                                                  bg="#FFFFFF", fg="#333",
                                                  relief="flat", bd=1)
        self.chat_box.pack(padx=15, pady=(15, 10))
        self.chat_box.insert(tk.END,
            "Miss Riverdale: Namaste ji! Main Riverdale bol rahi hoon — chai pee li? ☕\n\n")
        self.chat_box.config(state=tk.DISABLED)

        # ----- INPUT AREA -----
        inp = tk.Frame(root, bg=BG)
        inp.pack(pady=10)

        self.entry = tk.Entry(inp, width=50, font=("Segoe UI", 11),
                              bg="#FFFFFF", fg="#222",
                              relief="solid", bd=1)
        self.entry.grid(row=0, column=0, padx=10)
        self.entry.bind("<Return>", lambda e: self.on_send())

        tk.Button(inp, text="Send", bg=PRIMARY, fg="white",
                  activebackground="#0E2E2F",
                  font=("Segoe UI Semibold", 10),
                  relief="flat", width=12, cursor="hand2",
                  command=self.on_send).grid(row=0, column=1, padx=5)

        self.speak_btn = tk.Button(inp, text="🎤 Speak", bg=ACCENT, fg="white",
                                   activebackground="#AF8E4A",
                                   font=("Segoe UI Semibold", 10),
                                   relief="flat", width=12, cursor="hand2",
                                   command=self.toggle_voice_record)
        self.speak_btn.grid(row=0, column=2, padx=5)

        self.timer_label = tk.Label(inp, text="", bg=BG, fg="#555",
                                    font=("Segoe UI", 10))
        self.timer_label.grid(row=0, column=3, padx=(10, 0))

        # ----- FOOTER -----
        footer = tk.Frame(root, bg=BG)
        footer.pack(pady=5)
        tk.Label(footer,
                 text="© Riverwood Projects LLP | ‘We don’t just build homes, we build stories.’",
                 bg=BG, fg="#555", font=("Segoe UI", 9, "italic")).pack()

        threading.Thread(target=self.check_online_status, daemon=True).start()

    # ---- STATUS CHECK ----
    def check_online_status(self):
        if not OPENAI_API_KEY:
            self.online_status.set("⚪ Offline (no API key)")
            self.status_label.config(fg="lightgray")
            return
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            client.models.list()
            self.online_status.set("🟢 Online")
            self.status_label.config(fg="#7CFC00")
        except Exception:
            self.online_status.set("⚪ Offline")
            self.status_label.config(fg="lightgray")

    # ---- CHAT SYSTEM ----
    def append_message(self, sender, message):
        self.chat_box.config(state=tk.NORMAL)
        self.chat_box.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.yview(tk.END)

    def on_send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self.append_message("You", text)
        threading.Thread(target=self._reply, args=(text,), daemon=True).start()

    # ---- VOICE CONTROL ----
    def toggle_voice_record(self):
        if self._recording:
            # stop
            self._recording = False
            self.speak_btn.config(text="🎤 Speak", bg=ACCENT)
            self.timer_label.config(text="")
        else:
            # start
            self._recording = True
            self.record_seconds = 0
            self.speak_btn.config(text="⏹ Stop", bg="#C94C4C")
            threading.Thread(target=self.voice_record_thread, daemon=True).start()
            self.update_timer()

    def update_timer(self):
        if self._recording:
            self.record_seconds += 1
            self.timer_label.config(text=f"{self.record_seconds:02d} s", fg="red")
            self.root.after(1000, self.update_timer)

    def voice_record_thread(self):
        r = sr.Recognizer()
        text = ""
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio_chunks = []
                while self._recording:
                    try:
                        chunk = r.listen(source, timeout=0.5, phrase_time_limit=1)
                        audio_chunks.append(chunk)
                    except sr.WaitTimeoutError:
                        pass
                if audio_chunks:
                    data = sr.AudioData(b"".join(c.get_raw_data() for c in audio_chunks),
                                        audio_chunks[0].sample_rate,
                                        audio_chunks[0].sample_width)
                    try:
                        text = r.recognize_google(data, language="en-IN")
                    except Exception:
                        text = ""
        except Exception as e:
            print("🎤 Mic error:", e)

        # reset UI
        self._recording = False
        self.root.after(0, lambda: [
            self.speak_btn.config(text="🎤 Speak", bg=ACCENT),
            self.timer_label.config(text="")
        ])

        if text:
            self.append_message("You", text)
            self._reply(text)
        else:
            self.append_message("System", "Didn’t catch that, please try again.")

    # ---- AI RESPONSE ----
    def _reply(self, user_input):
        reply, self.memory = chat_with_ai(user_input, self.memory)
        self.append_message("Miss Riverdale", reply)
        speak(reply)


# ---- SAFE ENTRY POINT ----
if __name__ == "__main__":
    try:
        print(">>> Launching Miss Riverdale GUI...")
        root = tk.Tk()
        app = RiverdaleApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
