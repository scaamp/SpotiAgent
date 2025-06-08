import threading
import queue
import io
import sounddevice as sd
import soundfile as sf
import tempfile
import openai
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr

# Global command queue for communication between threads
command_queue = queue.Queue()

class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.listening = False
        self.listen_thread = None
        self.voice_command = None
        self.muted = False

    def start_listening(self):
        """Rozpocznij słuchanie w osobnym wątku"""
        if self.listening:
            return

        self.listening = True
        self.listen_thread = threading.Thread(target=self._listen_once)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        print("Nasłuchiwanie głosu aktywne - możesz mówić...")

    def stop_listening(self):
        """Zatrzymaj nasłuchiwanie"""
        self.listening = False
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1)
        print("Nasłuchiwanie zatrzymane.")

    def speak(self, text):
        """Wypowiedz tekst"""
        instructions = (
            "Mów jak entuzjastyczny, spokojny lektor radiowy. "
            "Brzmisz przyjaźnie i naturalnie, z lekkim uśmiechem w głosie. "
            "Zachowuj płynność, wyraź dykcję i nadaj rytm jak prezenter w radiu muzycznym. "
            "Nie przesadzaj z emocjami, ale brzmisz zaangażowanie. "
            "To Ty prowadzisz muzyczną rozmowę ze słuchaczem."
            )
        
        if self.muted:
            return
        # Wygeneruj mowę z tekstu
        response = openai.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="shimmer",
            input=text,
            speed=1.3,
            instructions=instructions
        )
        
        # Dodaj ciszę
        silence = AudioSegment.silent(duration=500)  # 0.5 sekundy
        audio_bytes = io.BytesIO(response.content)
        tts_audio = AudioSegment.from_file(audio_bytes, format="mp3")
        full_audio = silence + tts_audio
        play(full_audio)

    def _listen_once(self):
        """Jednorazowe nasłuchiwanie komendy głosowej"""
        try:
            with sr.Microphone() as source:
                print("Słucham... (powiedz komendę)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)

            try:
                text = self.recognizer.recognize_google(audio, language="pl-PL")
                if text:
                    print(f"Rozpoznano: {text}")
                    command_queue.put(text)
                    self.voice_command = text
            except sr.UnknownValueError:
                print("Nie rozpoznano mowy")
            except sr.RequestError as e:
                print(f"Błąd usługi rozpoznawania mowy: {e}")

        except Exception as e:
            print(f"Błąd podczas nasłuchiwania: {e}")

        # Automatycznie zatrzymaj nasłuchiwanie po wykonaniu
        self.listening = False 