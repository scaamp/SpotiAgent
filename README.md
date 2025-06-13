# 🎵 Spotify Voice Assistant with GPT-4

A voice-controlled assistant that integrates with Spotify and OpenAI GPT-4. It enables natural language music control in both English and Polish.

---

## 🧰 Features

* 🎤 Voice recognition via Google Speech Recognition
* 🔊 Text-to-speech responses (pyttsx3)
* 🎵 Spotify control: play, pause, next, like
* 🌟 Mood-based recommendations ("play something chill")
* 📲 Device switching (TV, Computer, Smartphone)
* 🔊 Volume control (up/down/set value)
* 🔒 OAuth 2.0 with token refresh
* ⚖️ Natural language parser using GPT-4 that converts speech into JSON actions

---

## 🔧 Installation

### 1. Clone the repository

```bash
git clone https://github.com/scaamp/SpotiAgent.git
cd SpotiAgent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a `.env` file

```ini
OPENAI_API_KEY=your_openai_key
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

---

## ▶️ Running the Assistant

Text mode:

```bash
python main.py
```

Voice mode:

```bash
python main.py --voice
```

---

## 🔊 Sample Commands

* "Play Blinding Lights by The Weeknd"
* "Next"
* "Pause music"
* "Volume up by 10"
* "Switch to TV"
* "Like this song"
* "I need something chill"

---

## 🧵 Architecture Overview

```
Voice/Text Input
     ⬇️
Speech Recognition
     ⬇️
GPT-4 Parser (JSON Action)
     ⬇️
Spotify API Execution
     ⬇️
TTS Audio Feedback
```

---

## 📃 Notes

* Requires a Spotify Premium account
* Supports both English and Polish commands
* Tokens saved to `spotify_tokens.json` for reuse

---

## ✏️ Roadmap

* [ ] GUI (Streamlit or tkinter)
* [ ] User memory/profile
* [ ] Chat history
* [ ] Voice cloning (e.g., ElevenLabs)
* [ ] Transcription and logging

---

## 📆 License

MIT License © 2025 Jakub

---

# 🎵 Asystent Głosowy Spotify z GPT-4

Asystent sterowany głosem, integrujący się z Spotify i GPT-4. Pozwala sterować muzyką za pomocą języka naturalnego po angielsku i polsku.

---

## 🧰 Funkcjonalności

* 🎤 Rozpoznawanie mowy (Google Speech Recognition)
* 🔊 Synteza mowy (pyttsx3)
* 🎵 Sterowanie Spotify: play, pauza, następna, polubienia
* 🌟 Rekomendacje na podstawie nastroju ("zagraj coś spokojnego")
* 📲 Przełączanie urządzeń (TV, Komputer, Telefon)
* 🔊 Regulacja głośności (w górę/w dół/konkretna wartość)
* 🔒 OAuth 2.0 z odświeżaniem tokena
* ⚖️ Parser poleceń na bazie GPT-4 (JSON z akcją + parametrami)

---

## 🔧 Instalacja

### 1. Klonowanie repozytorium

```bash
git clone https://github.com/scaamp/SpotiAgent.git
cd SpotiAgent
```

### 2. Instalacja zależności

```bash
pip install -r requirements.txt
```

### 3. Utwórz plik `.env`

```ini
OPENAI_API_KEY=twój_klucz_openai
SPOTIFY_CLIENT_ID=twój_client_id
SPOTIFY_CLIENT_SECRET=twój_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

---

## ▶️ Uruchamianie

Tryb tekstowy:

```bash
python main.py
```

Tryb głosowy:

```bash
python main.py --voice
```

---

## 🔊 Przykładowe komendy

* "Włącz piosenkę Blinding Lights od The Weeknd"
* "Następna"
* "Zatrzymaj muzykę"
* "Podgłoś o 10"
* "Przełącz na telewizor"
* "Dodaj do ulubionych"
* "Potrzebuję czegoś spokojnego"

---

## 🧵 Architektura

```
Wejście Głos/Text
     ⬇️
Rozpoznanie mowy
     ⬇️
Parser GPT-4 (JSON Akcja)
     ⬇️
Spotify API
     ⬇️
Synteza mowy (pyttsx3)
```

---


## 📃 Notatki

* Wymagane konto Spotify Premium
* Obsługa języka angielskiego i polskiego
* Tokeny zapisane w `spotify_tokens.json` (automatyczne odświeżanie)

---

## ✏️ Plan rozwoju

* [ ] GUI (Streamlit lub tkinter)
* [ ] Pamięć i profil użytkownika
* [ ] Historia czatu
* [ ] Klonowanie głosu (np. ElevenLabs)
* [ ] Zapis transkrypcji i logów
