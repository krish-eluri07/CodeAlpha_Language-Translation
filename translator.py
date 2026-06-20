import tkinter as tk
import customtkinter as ctk
from deep_translator import GoogleTranslator
from gtts import gTTS
import os
import threading
import pygame
import time

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Set the theme and color options
ctk.set_appearance_mode("System")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")

class TranslationApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure Window
        self.title("Language Translator")
        self.geometry("700x550")
        self.resizable(False, False)

        # Language Mapping (Display Name -> Code)
        self.languages = {
            "English": "en", "Spanish": "es", "French": "fr", "German": "de",
            "Hindi": "hi", "Chinese (Simplified)": "zh-CN", "Arabic": "ar",
            "Russian": "ru", "Japanese": "ja", "Portuguese": "pt", "Italian": "it"
        }
        self.lang_list = list(self.languages.keys())
        self.current_audio_file = None

        self.setup_ui()
        
        # Clean up any leftover temp files on close
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # --- Title ---
        self.title_label = ctk.CTkLabel(self, text="LANGUAGE TRANSLATOR", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=20)

        # --- Main Layout Frame ---
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # Left Side: Input
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10)

        self.src_lang_combo = ctk.CTkComboBox(self.left_frame, values=["Auto Detect"] + self.lang_list, width=180)
        self.src_lang_combo.set("Auto Detect")
        self.src_lang_combo.pack(pady=10)

        self.input_text = ctk.CTkTextbox(self.left_frame, width=280, height=200, font=("Helvetica", 14))
        self.input_text.pack(pady=5, padx=10, fill="both", expand=True)

        # Right Side: Output
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10)

        self.tgt_lang_combo = ctk.CTkComboBox(self.right_frame, values=self.lang_list, width=180)
        self.tgt_lang_combo.set("Spanish")
        self.tgt_lang_combo.pack(pady=10)

        self.output_text = ctk.CTkTextbox(self.right_frame, width=280, height=200, font=("Helvetica", 14))
        self.output_text.configure(state="disabled") # Read-only initially
        self.output_text.pack(pady=5, padx=10, fill="both", expand=True)

        # --- Action Buttons Frame ---
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=40, pady=20)

        # Translate Button
        self.translate_btn = ctk.CTkButton(self.btn_frame, text="Translate", command=self.start_translation, font=ctk.CTkFont(weight="bold"), width=150)
        self.translate_btn.pack(side="left", padx=10)

        # Copy Button
        self.copy_btn = ctk.CTkButton(self.btn_frame, text="📋 Copy Output", fg_color="gray", hover_color="#555555", command=self.copy_to_clipboard, width=120)
        self.copy_btn.pack(side="left", padx=10)

        # Text to Speech Button
        self.tts_btn = ctk.CTkButton(self.btn_frame, text="🔊 Listen", fg_color="gray", hover_color="#555555", command=self.start_tts, width=120)
        self.tts_btn.pack(side="left", padx=10)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Ready", font=("Helvetica", 12), text_color="gray")
        self.status_label.pack(side="bottom", pady=5)

    # --- Core Logic Functions ---

    def translate_logic(self):
        try:
            text_to_translate = self.input_text.get("1.0", tk.END).strip()
            if not text_to_translate:
                self.update_status("Please enter some text to translate.", "red")
                return

            self.update_status("Translating...", "yellow")

            src_lang_name = self.src_lang_combo.get()
            tgt_lang_name = self.tgt_lang_combo.get()

            src_code = "auto" if src_lang_name == "Auto Detect" else self.languages[src_lang_name]
            tgt_code = self.languages[tgt_lang_name]

            # API Call
            translated = GoogleTranslator(source=src_code, target=tgt_code).translate(text_to_translate)

            # Update UI
            self.output_text.configure(state="normal")
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", translated)
            self.output_text.configure(state="disabled")

            self.update_status("Translation successful!", "green")
        except Exception as e:
            self.update_status(f"Error: {str(e)}", "red")

    def start_translation(self):
        threading.Thread(target=self.translate_logic, daemon=True).start()

    def copy_to_clipboard(self):
        translated_text = self.output_text.get("1.0", tk.END).strip()
        if translated_text:
            self.clipboard_clear()
            self.clipboard_append(translated_text)
            self.update_status("Copied to clipboard!", "green")

    def tts_logic(self):
        text = self.output_text.get("1.0", tk.END).strip()
        if not text:
            self.update_status("Nothing to speak.", "red")
            return
        
        try:
            self.update_status("Generating Audio...", "yellow")
            tgt_lang_name = self.tgt_lang_combo.get()
            tgt_code = self.languages[tgt_lang_name]

            # 1. Stop and completely unload any playing audio to release the file lock
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

            # 2. Use a unique timestamped filename to completely bypass file access conflicts
            filename = f"speech_{int(time.time())}.mp3"
            
            # Generate and save new speech audio
            tts = gTTS(text=text, lang=tgt_code)
            tts.save(filename)
            
            # Play new file
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # 3. Track old files and delete them safely
            if self.current_audio_file and os.path.exists(self.current_audio_file):
                try:
                    os.remove(self.current_audio_file)
                except Exception:
                    pass # Ignore if OS hasn't unlocked it yet; it'll catch on app exit
            
            self.current_audio_file = filename
            self.update_status("Playing audio...", "green")
        except Exception as e:
            self.update_status("Audio not supported or failed to generate.", "red")

    def start_tts(self):
        threading.Thread(target=self.tts_logic, daemon=True).start()

    def update_status(self, text, color):
        color_map = {"green": "#2ecc71", "red": "#e74c3c", "yellow": "#f1c40f", "gray": "gray"}
        # CustomTkinter automatically handles thread-safe rendering for configure()
        self.status_label.configure(text=text, text_color=color_map.get(color, "white"))

    def on_closing(self):
        # Final cleanup routine when closing the window
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                os.remove(self.current_audio_file)
            except Exception:
                pass
        self.destroy()

if __name__ == "__main__":
    app = TranslationApp()
    app.mainloop()