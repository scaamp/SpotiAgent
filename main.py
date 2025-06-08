import sys
import time
import queue
from spotify_auth import get_token
from voice_recognizer import VoiceRecognizer, command_queue
from spotify_controller import process_command

def main(start_in_voice_mode=False):
    # Inicjalizacja rozpoznawania głosu
    voice_agent = VoiceRecognizer()

    # Pobierz token dostępu z automatycznym odświeżaniem
    access_token = get_token()

    if not access_token:
        print("Nie udało się uzyskać tokena dostępu. Kończenie.")
        return

    voice_agent.speak("Agent Spotify gotowy. Wpisz komendę lub naciśnij 'Q' aby użyć komendy głosowej.")

    # Główna pętla
    try:
        while True:
            if start_in_voice_mode:
                voice_agent.start_listening()
                # Czekaj na zakończenie nasłuchiwania
                while voice_agent.listening:
                    time.sleep(0.1)

                # Sprawdź czy jest komenda głosowa
                try:
                    voice_command = command_queue.get_nowait()
                    print(f"Wykonuję komendę głosową: {voice_command}")
                    process_command(voice_command, access_token, voice_agent)
                    start_in_voice_mode = False
                except queue.Empty:
                    print("Nie rozpoznano komendy głosowej")
                    voice_agent.speak("Nie rozpoznano komendy głosowej. Wracam do trybu tekstowego.")
                    start_in_voice_mode = False
            else:
                # Wyświetl instrukcję
                print("\nWprowadź komendę (lub 'Q' aby przełączyć na tryb głosowy, 'exit' aby wyjść):")
                user_input = input("> ")

                if user_input.lower() == 'mute':
                    voice_agent.muted = True
                    print("Agent został wyciszony")

                elif user_input.lower() == 'unmute':
                    voice_agent.muted = False
                    print("Agent został odciszony")

                elif user_input.lower() == 'exit':
                    print("Kończenie programu...")
                    break

                elif user_input.lower() == 'q':
                    print("Przełączam na tryb głosowy...")
                    voice_agent.speak("Tryb głosowy aktywny. Proszę wydać komendę.")
                    voice_agent.start_listening()

                    # Czekaj na zakończenie nasłuchiwania
                    while voice_agent.listening:
                        time.sleep(0.1)

                    # Sprawdź czy jest komenda głosowa
                    try:
                        voice_command = command_queue.get_nowait()
                        print(f"Wykonuję komendę głosową: {voice_command}")
                        process_command(voice_command, access_token, voice_agent)
                    except queue.Empty:
                        print("Nie rozpoznano komendy głosowej")
                        voice_agent.speak("Nie rozpoznano komendy głosowej. Wracam do trybu tekstowego.")

                    # Wróć do trybu tekstowego
                    print("Wracam do trybu tekstowego")

                elif user_input:
                    # Wykonaj komendę tekstową
                    process_command(user_input, access_token, voice_agent)

    finally:
        # Zatrzymaj rozpoznawanie głosu przy zamykaniu
        voice_agent.stop_listening()

if __name__ == "__main__":
    start_in_voice_mode = False

    if len(sys.argv) > 1:
        if sys.argv[1] == "--voice":
            start_in_voice_mode = True

    main(start_in_voice_mode=start_in_voice_mode)
