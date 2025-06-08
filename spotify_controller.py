import json
import time
import requests
from openai import OpenAI
import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_user_input(user_input):
    prompt = f"""
    <rules>
    You are an AI music assistant.
    Extract the following user input into structured JSON.
    If the user wants to play a specific song, extract the song and artist (if provided).
    If the user says things like "next", "next song", "another", "kolejna", "następna", return another JSON format with action "next_song" and leave song and artist as empty strings.
    If the user says things like "stop", "pause", "zatrzymaj", "pauza", "wstrzymaj", "stop playing". IGNORE command "mute", because it isn NOT VALID for this case. Return JSON format with action "pause_playback".
    If the user says things like "resume", "play", "wznów", "kontynuuj", "graj", "start", "play again", "continue", return JSON format with action "resume_playback".
    If the user describes their mood or emotion, or asks for music that matches their current state or favourite genre (e.g. "I'm feeling happy", "play techno", "włącz rock", "uwielbiam pop", "play something energetic", "need calm music", "mam dobry humor", "chcę coś energicznego", "mam dziś doła", "nienawidzę świata"), return JSON format with action "recommendation".
    If the user says things like "switch device to TV", "przelacz na telewizor", "przelacz na komputer", "Wlacz na telefonie", "komputer", "telewizor", "odpal na TV", "graj na TV", "turn on TV", return JSON format with action "switch_device" and "device: TV|Smartphone|Computer". Only these values are acceptable.
    If the user says things like "I like this song", "mi się podoba", "fajna piosenka", "dodaj do ulubionych", "like this song", "polub tę piosenkę", "lubię to", "podoba mi się", "save this song", "love this track", "add to favorites", "favourite", "add to liked songs", return JSON format with action "like".
    If the user says things like "Volume up", "Volume down", "Podgłos troche", "Przycisz", "Dopierdol teraz glosniej", "Ciszej tam kurwa", "Mozesz odrobine glosniej?", "Could you more louder?" "Set volume to 50", "Ustaw glosnosc na 30", return JSON format with action "volume_up|volume_down|set_volume" and "volume": "X", where X is the value that you should recognize based on user input.
    If song or artist are missing for play_song action, set them as empty strings.
    ONLY return valid JSON without any comments, explanations, or additional text.
    </rules>
    User input:
    "{user_input}"

    JSON format:
    <examples>
    For select song:
    {{
        "action": "play_song",
        "song": "...",
        "artist": "..."
    }}

    For skipping to next song:
    {{
        "action": "next_song"
    }}

    For pausing playback:
    {{
        "action": "pause_playback"
    }}

    For resume song:
    {{
        "action": "resume_playback"
    }}

    For mood-based recommendation:
    {{
        "action": "recommendation"
    }}
    
    For switching:
    {{
        "action": "switch_device",
        "device: "TV|Computer|Smartphone"
    }}
    
    For liking current song:
    {{
        "action": "like"
    }}
    
    For increasing volume:
    {{
        "action": "volume_up",
        "volume": "10"
    }}
    
    For decreasing volume:
    {{
        "action": "volume_down",
        "volume": "10"
    }}
    
    For setting specific volume:
    {{
        "action": "set_volume",
        "volume": "X"
    }}
    </examples>
    """

    client = OpenAI(
        api_key=openai.api_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        # Bezpieczniejsza metoda niż eval()
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        print("Błąd dekodowania JSON z odpowiedzi GPT")
        # Próbujemy usunąć dodatkowe znaki, które czasem występują w odpowiedzi
        content = response.choices[0].message.content
        content = content.strip()
        # Znajdź początek i koniec JSON
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end])
            except:
                pass

        # Sprawdź czy komenda dotyczy następnej piosenki
        if any(keyword in user_input.lower() for keyword in ["następny", "następna", "next", "skip", "pomiń", "dalej"]):
            return {"action": "next_song"}

        elif any(keyword in user_input.lower() for keyword in
                 ["stop", "pause", "zatrzymaj", "pauza", "wstrzymaj", "przestań"]):
            return {"action": "pause_playback"}

        # A w sekcji obsługi błędów JSONDecodeError, po warunkach dla next i pause:
        elif any(keyword in user_input.lower() for keyword in
                 ["resume", "play", "wznów", "kontynuuj", "graj", "start", "continue"]):
            return {"action": "resume_playback"}

        elif any(keyword in user_input.lower() for keyword in
                 ["podoba mi się", "like", "lubię to", "fajna piosenka", "dodaj do ulubionych", "polub"]):
            return {"action": "like"}

        # Domyślna odpowiedź jeśli nie udało się sparsować
        return {"action": "play_song", "song": user_input, "artist": ""}

def search_and_play_playlist(mood_input, access_token, voice_agent=None):
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # 1. Search playlist by mood_input
        search_url = "https://api.spotify.com/v1/search"
        params = {
            "q": mood_input,
            "type": "playlist",
            "limit": 5
        }

        response = requests.get(search_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Błąd wyszukiwania playlisty: {response.status_code}")
            print(response.text)
            if voice_agent:
                voice_agent.speak("Nie udało się wyszukać playlisty.")
            return False

        playlists_data = response.json()
        playlists = playlists_data.get("playlists", {}).get("items", [])

        # 2. Filter playlists owned by Spotify
        selected_playlist = None

        # 3. If no playlist from Spotify, pick any available
        if not selected_playlist and playlists:
            selected_playlist = playlists[0]

        if not selected_playlist:
            print("Nie znaleziono pasującej playlisty.")
            if voice_agent:
                voice_agent.speak("Nie znalazłem żadnej playlisty pasującej do Twojego nastroju.")
            return False

        playlist_id = selected_playlist["id"]
        playlist_name = selected_playlist["name"]
        context_uri = selected_playlist["uri"]

        response_text = f"Dodaję playlistę {playlist_name}."
        print(response_text)
        if voice_agent:
            voice_agent.speak(response_text)

        # 4. Play playlist
        play_url = "https://api.spotify.com/v1/me/player/play"
        payload = {
            "context_uri": context_uri
        }

        play_response = requests.put(play_url, headers=headers, json=payload)

        if play_response.status_code not in [200, 204]:
            print(f"Błąd odtwarzania playlisty: {play_response.status_code}")
            print(play_response.text)
            if voice_agent:
                voice_agent.speak("Nie udało się odtworzyć playlisty.")
            return False

        print(f"✅ Playlistę '{playlist_name}' rozpoczęto pomyślnie!")
        return True

    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        import traceback
        traceback.print_exc()
        if voice_agent:
            voice_agent.speak("Wystąpił błąd podczas odtwarzania playlisty.")
        return False

def pause_playback(access_token):
    """Zatrzymanie odtwarzania"""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Pobierz aktualnie odtwarzany utwór (do wyświetlenia informacji)
    current_playing_url = "https://api.spotify.com/v1/me/player/currently-playing"
    current_response = requests.get(current_playing_url, headers=headers)

    if current_response.status_code == 200 and current_response.content:
        current_data = current_response.json()
        if current_data.get('item'):
            current_track_name = current_data['item']['name']
            current_artist_name = current_data['item']['artists'][0]['name']

            # Wywołaj endpoint pause
            pause_url = "https://api.spotify.com/v1/me/player/pause"
            response = requests.put(pause_url, headers=headers)

            print(f"Status zatrzymania odtwarzania: {response.status_code}")

            return {
                "success": response.status_code in [200, 204],
                "paused_track": f"{current_track_name} - {current_artist_name}"
            }

    return {
        "success": False,
        "paused_track": "Brak odtwarzanego utworu"
    }

def resume_playback(access_token):
    """Wznowienie odtwarzania"""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Pobierz aktualnie zapauzowany utwór (do wyświetlenia informacji)
    current_playing_url = "https://api.spotify.com/v1/me/player/currently-playing"
    current_response = requests.get(current_playing_url, headers=headers)

    current_track_name = "nieznany utwór"
    current_artist_name = "nieznany artysta"

    if current_response.status_code == 200 and current_response.content:
        current_data = current_response.json()
        if current_data.get('item'):
            current_track_name = current_data['item']['name']
            current_artist_name = current_data['item']['artists'][0]['name']

    # Wywołaj endpoint play
    resume_url = "https://api.spotify.com/v1/me/player/play"
    response = requests.put(resume_url, headers=headers)

    print(f"Status wznowienia odtwarzania: {response.status_code}")

    return {
        "success": response.status_code in [200, 204],
        "resumed_track": f"{current_track_name} - {current_artist_name}"
    }

def next_song(access_token):
    """Przejście do następnego utworu"""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # Pobierz aktualnie odtwarzany utwór (do wyświetlenia informacji)
    current_playing_url = "https://api.spotify.com/v1/me/player/currently-playing"
    current_response = requests.get(current_playing_url, headers=headers)

    current_track_name = "nieznany utwór"
    current_artist_name = "nieznany artysta"

    if current_response.status_code == 200 and current_response.content:
        current_data = current_response.json()
        if current_data.get('item'):
            current_track_name = current_data['item']['name']
            current_artist_name = current_data['item']['artists'][0]['name']

    # Wywołaj endpoint next
    next_url = "https://api.spotify.com/v1/me/player/next"
    response = requests.post(next_url, headers=headers)

    print(f"Status przejścia do następnego utworu: {response.status_code}")

    # Poczekaj chwilę, aby Spotify zaktualizował informacje o odtwarzaniu
    time.sleep(1)

    # Pobierz informacje o nowym utworze
    new_response = requests.get(current_playing_url, headers=headers)

    new_track_name = "nieznany utwór"
    new_artist_name = "nieznany artysta"

    if new_response.status_code == 200 and new_response.content:
        new_data = new_response.json()
        if new_data.get('item'):
            new_track_name = new_data['item']['name']
            new_artist_name = new_data['item']['artists'][0]['name']

    return {
        "success": response.status_code in [200, 204],
        "previous_track": f"{current_track_name} - {current_artist_name}",
        "current_track": f"{new_track_name} - {new_artist_name}"
    }

def search_song(song, artist, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    query = f"{song} {artist}"
    print(f"Wyszukiwanie: {query}")

    response = requests.get(
        f"https://api.spotify.com/v1/search",
        headers=headers,
        params={"q": query, "type": "track", "limit": 1}
    )

    if response.status_code != 200:
        print(f"Błąd wyszukiwania: {response.status_code}")
        print(response.text)
        raise Exception(f"Błąd API Spotify: {response.status_code}")

    data = response.json()

    if not data['tracks']['items']:
        raise Exception(f"Nie znaleziono utworu: {song} {artist}")

    track_id = data['tracks']['items'][0]['id']
    track_name = data['tracks']['items'][0]['name']
    artist_name = data['tracks']['items'][0]['artists'][0]['name']
    print(f"Znaleziono utwór: {track_name} - {artist_name} (ID: {track_id})")

    return track_id

def play_song(track_id, access_token, voice_agent=None):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Pobierz dostępne urządzenia
    devices_response = requests.get(
        "https://api.spotify.com/v1/me/player/devices",
        headers=headers
    )

    if devices_response.status_code != 200:
        print(f"Błąd pobierania urządzeń: {devices_response.status_code}")
        print(devices_response.text)
        return False

    devices_data = devices_response.json()
    print(f"Znalezione urządzenia: {json.dumps(devices_data, indent=2)}")

    if devices_data.get('devices') and len(devices_data['devices']) > 0:
        active_devices = [d for d in devices_data['devices'] if d.get('is_active')]

        if active_devices:
            device_id = active_devices[0]['id']
            print(f"Używam aktywnego urządzenia: {active_devices[0]['name']} ({device_id})")
        else:
            device_id = devices_data['devices'][0]['id']
            print(f"Aktywuję urządzenie: {devices_data['devices'][0]['name']} ({device_id})")

            # Aktywuj urządzenie
            transfer_response = requests.put(
                "https://api.spotify.com/v1/me/player",
                headers=headers,
                json={"device_ids": [device_id], "play": True}
            )
            print(f"Status aktywacji urządzenia: {transfer_response.status_code}")
            if transfer_response.status_code not in [200, 204]:
                print(f"Odpowiedź: {transfer_response.text}")

            # Zaczekaj chwilę
            time.sleep(2)

        # Zamiast używać API rekomendacji, użyjemy kontekstu radia utworu
        # Ta metoda uruchamia automatyczne odtwarzanie podobnych utworów (tzw. Spotify Radio)
        print(f"Uruchamiam odtwarzanie utworu {track_id}")

        # Sposób 1: Użyj normalnego odtwarzania, ale z ustawionym flag kontekstu
        play_url = f"https://api.spotify.com/v1/me/player/play"
        if device_id:
            play_url += f"?device_id={device_id}"

        # Najpierw odtwórz konkretny utwór
        payload = {
            "uris": [f"spotify:track:{track_id}"]
        }

        response = requests.put(
            play_url,
            headers=headers,
            json=payload
        )

        time.sleep(1)
        playing_response = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers=headers
        )

        if response.status_code not in [200, 204]:
            print(f"Odpowiedź: {response.text}")
            return False

        # Następnie zapytaj użytkownika czy chce dodać podobne utwory do kolejki
        if voice_agent:
            voice_agent.speak("Czy chcesz, żebym dodał podobne utwory do kolejki? Odpowiedz tak lub nie.")
            print("Czy chcesz, żebym dodał podobne utwory do kolejki? (tak/nie)")
            
            # Poczekaj na odpowiedź użytkownika
            while True:
                try:
                    user_input = input("> ").lower()
                    if user_input in ['tak', 't', 'yes', 'y']:
                        add_similar = True
                        break
                    elif user_input in ['nie', 'n', 'no']:
                        add_similar = False
                        break
                    else:
                        print("Proszę odpowiedzieć 'tak' lub 'nie'")
                        if voice_agent:
                            voice_agent.speak("Proszę odpowiedzieć tak lub nie")
                except KeyboardInterrupt:
                    add_similar = False
                    break

            if add_similar:
                # Pobierz ID artysty dla tego utworu
                track_info_url = f"https://api.spotify.com/v1/tracks/{track_id}"
                track_response = requests.get(track_info_url, headers=headers)

                if track_response.status_code == 200:
                    track_data = track_response.json()
                    artist_id = track_data['artists'][0]['id']

                    # Pobierz najpopularniejsze utwory artysty
                    artist_top_tracks_url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US"
                    top_tracks_response = requests.get(artist_top_tracks_url, headers=headers)

                    if top_tracks_response.status_code == 200:
                        top_tracks_data = top_tracks_response.json()

                        # Dodaj 10 najpopularniejszych utworów do kolejki
                        for track in top_tracks_data.get('tracks', [])[:10]:
                            if track['id'] != track_id:  # Nie dodawaj ponownie aktualnego utworu
                                queue_url = "https://api.spotify.com/v1/me/player/queue"
                                queue_params = {"uri": track['uri']}
                                queue_response = requests.post(
                                    queue_url,
                                    headers=headers,
                                    params=queue_params
                                )

                                if queue_response.status_code in [200, 204]:
                                    print(f"Dodano do kolejki: {track['name']} - {track['artists'][0]['name']}")
                                else:
                                    print(f"Błąd dodawania do kolejki: {queue_response.status_code}")
                                    print(queue_response.text)
                    else:
                        print(f"Błąd pobierania popularnych utworów: {top_tracks_response.status_code}")
                else:
                    print(f"Błąd pobierania informacji o utworze: {track_response.status_code}")

        # Sposób 2 (alternatywny): Włącz tryb shuffle
        shuffle_url = "https://api.spotify.com/v1/me/player/shuffle"
        shuffle_params = {"state": "true"}
        if device_id:
            shuffle_params["device_id"] = device_id

        shuffle_response = requests.put(
            shuffle_url,
            headers=headers,
            params=shuffle_params
        )

        print(f"Status włączania shuffle: {shuffle_response.status_code}")

        return True
    else:
        print("Nie znaleziono urządzeń. Proszę otworzyć aplikację Spotify.")
        return False

def switch_device(access_token, device_type_target, voice_agent=None):
    """Przełącza odtwarzanie na urządzenie o wskazanym typie (TV, Computer, Smartphone)"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    devices_url = "https://api.spotify.com/v1/me/player/devices"
    devices_response = requests.get(devices_url, headers=headers)

    if devices_response.status_code != 200:
        print(f"Błąd pobierania urządzeń: {devices_response.status_code}")
        if voice_agent:
            voice_agent.speak("Nie udało się pobrać listy urządzeń.")
        return False

    devices_data = devices_response.json()

    # Dopasuj urządzenie po typie (ignorując wielkość liter)
    target_device = None
    for device in devices_data.get('devices', []):
        if device['type'].lower() == device_type_target.lower():
            target_device = device
            break

    if not target_device:
        print(f"Nie znaleziono urządzenia typu {device_type_target}.")
        if voice_agent:
            voice_agent.speak(f"Nie znalazłem urządzenia typu {device_type_target}.")
        return False

    device_id = target_device['id']

    # Przełącz urządzenie
    transfer_url = "https://api.spotify.com/v1/me/player"
    transfer_payload = {
        "device_ids": [device_id],
        "play": True
    }

    transfer_response = requests.put(transfer_url, headers=headers, json=transfer_payload)

    if transfer_response.status_code in [200, 204]:
        print(f"Przełączono na urządzenie: {target_device['name']} ({device_type_target})")
        if voice_agent:
            voice_agent.speak(f"Przełączono na {target_device['name']}")
        return True
    else:
        print(f"Błąd przełączania urządzenia: {transfer_response.status_code}")
        if voice_agent:
            voice_agent.speak("Nie udało się przełączyć urządzenia.")
        return False

def get_current_song(access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    time.sleep(1)
    playing_response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers=headers
    )
    if playing_response.status_code == 200:
        playing_data = playing_response.json()
        name = playing_data['item']['name']
        artists = ", ".join([artist['name'] for artist in playing_data['item']['artists']])
        return f"Teraz odtwarzane: {name} – {artists}"
    else:
        print("🔍 Nie udało się pobrać informacji o odtwarzanym utworze.")

def like_current_song(access_token, voice_agent=None):
    """Polubienie aktualnie odtwarzanej piosenki"""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # 1. Pobierz aktualnie odtwarzany utwór
    current_playing_url = "https://api.spotify.com/v1/me/player/currently-playing"
    current_response = requests.get(current_playing_url, headers=headers)

    if current_response.status_code != 200 or not current_response.content:
        print("Brak aktualnie odtwarzanego utworu lub błąd odpowiedzi.")
        if voice_agent:
            voice_agent.speak("Nie mogę znaleźć aktualnie odtwarzanego utworu.")
        return {
            "success": False,
            "track_info": None,
            "already_liked": False
        }

    current_data = current_response.json()
    if not current_data.get('item'):
        print("Brak informacji o odtwarzanym utworze.")
        if voice_agent:
            voice_agent.speak("Nie mogę znaleźć informacji o odtwarzanym utworze.")
        return {
            "success": False,
            "track_info": None,
            "already_liked": False
        }

    track_id = current_data['item']['id']
    track_name = current_data['item']['name']
    artist_name = current_data['item']['artists'][0]['name']
    track_info = f"{track_name} - {artist_name}"

    # 2. Sprawdź, czy utwór jest już polubiony
    check_url = f"https://api.spotify.com/v1/me/tracks/contains"
    check_params = {"ids": track_id}
    check_response = requests.get(check_url, headers=headers, params=check_params)

    if check_response.status_code == 200:
        is_saved = check_response.json()
        if is_saved and is_saved[0]:
            print(f"ℹ️ Utwór {track_info} jest już polubiony.")
            return {
                "success": True,
                "track_info": track_info,
                "already_liked": True
            }

    # 3. Dodaj utwór do polubionych, jeśli nie jest już polubiony
    save_url = f"https://api.spotify.com/v1/me/tracks"
    save_params = {"ids": track_id}
    save_response = requests.put(save_url, headers=headers, params=save_params)

    success = save_response.status_code in [200, 201, 204]

    if success:
        print(f"✅ Polubiono utwór: {track_info}")
    else:
        print(f"❌ Błąd polubienia utworu: {save_response.status_code}")
        print(save_response.text)

    return {
        "success": success,
        "track_info": track_info,
        "already_liked": False
    }

def set_volume(access_token, volume_level=None, adjust_by=None, voice_agent=None):
    """
    Ustawia głośność odtwarzania Spotify.

    Parametry:
    - volume_level: konkretny poziom głośności (0-100)
    - adjust_by: wartość do zwiększenia/zmniejszenia głośności
    - voice_agent: opcjonalny agent głosowy

    Zwraca słownik z informacją o sukcesie i poziomem głośności.
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # 1. Pobierz aktualny poziom głośności
    player_url = "https://api.spotify.com/v1/me/player"
    player_response = requests.get(player_url, headers=headers)

    if player_response.status_code != 200 or not player_response.content:
        print("Błąd pobierania stanu odtwarzacza.")
        if voice_agent:
            voice_agent.speak("Nie mogę pobrać informacji o odtwarzaczu.")
        return {
            "success": False,
            "volume": None
        }

    player_data = player_response.json()
    current_volume = player_data.get('device', {}).get('volume_percent', 50)

    # 2. Oblicz nowy poziom głośności
    if volume_level is not None:
        # Ustaw konkretny poziom głośności
        new_volume = volume_level
    elif adjust_by is not None:
        # Zwiększ/zmniejsz głośność o podaną wartość
        new_volume = current_volume + adjust_by
    else:
        return {
            "success": False,
            "volume": current_volume
        }

    # 3. Upewnij się, że wartość jest w zakresie 0-100
    new_volume = max(0, min(100, new_volume))

    # 4. Ustaw nowy poziom głośności
    volume_url = "https://api.spotify.com/v1/me/player/volume"
    volume_params = {"volume_percent": new_volume}
    volume_response = requests.put(volume_url, headers=headers, params=volume_params)

    success = volume_response.status_code in [200, 204]

    if success:
        print(f"✅ Ustawiono głośność na {new_volume}%")
        if voice_agent:
            if adjust_by is not None and adjust_by > 0:
                voice_agent.speak(f"Zwiększono głośność do {new_volume} procent")
            elif adjust_by is not None and adjust_by < 0:
                voice_agent.speak(f"Zmniejszono głośność do {new_volume} procent")
            else:
                voice_agent.speak(f"Ustawiono głośność na {new_volume} procent")
    else:
        print(f"❌ Błąd ustawiania głośności: {volume_response.status_code}")
        print(volume_response.text)
        if voice_agent:
            voice_agent.speak("Nie udało się zmienić głośności")

    return {
        "success": success,
        "volume": new_volume if success else current_volume
    }

def process_command(command, access_token, voice_agent):
    """Przetwarzanie komendy (tekstowej lub głosowej)"""
    try:
        # Dodaj debug
        print(f"Rozpoczynam przetwarzanie komendy: {command}")

        # Parsowanie komendy
        parsed = parse_user_input(command)
        print(f"Sparsowana komenda: {parsed}")

        # Obsługa różnych typów komend
        if parsed.get('action') == 'next_song':
            print("Przechodzę do następnego utworu...")
            if voice_agent:
                voice_agent.speak("Przechodzę do następnego utworu")

            result = next_song(access_token)

            if result['success']:
                response_text = f"Pominięto utwór {result['previous_track']}. Teraz odtwarzam {result['current_track']}"
            else:
                response_text = "Nie udało się przejść do następnego utworu. Sprawdź czy aplikacja Spotify jest aktywna."

            print(response_text)
            if voice_agent:
                voice_agent.speak(response_text)

            return result['success']

        elif parsed.get('action') == 'play_song':  # domyślnie 'play_song'
            # Informacja dla użytkownika
            response_text = f"Szukam utworu '{parsed['song']}' artysty {parsed['artist']}..."
            print(response_text)
            if voice_agent:
                voice_agent.speak(response_text)

            # Wyszukaj i odtwórz
            print("Rozpoczynam wyszukiwanie utworu...")
            track_id = search_song(parsed['song'], parsed['artist'], access_token)
            print(f"Znaleziono ID utworu: {track_id}")

            print("Próbuję odtworzyć utwór...")
            success = play_song(track_id, access_token, voice_agent)

            # Odpowiedź
            if success:
                response_text = get_current_song(access_token)
            else:
                response_text = "Nie mogę odtworzyć - sprawdź czy aplikacja Spotify jest otwarta."

            print(response_text)
            if voice_agent:
                voice_agent.speak(response_text)

            return success

        elif parsed.get('action') == 'pause_playback':
            print("Zatrzymuję odtwarzanie...")
            if voice_agent:
                voice_agent.speak("Zatrzymuję odtwarzanie")

            result = pause_playback(access_token)

            if result['success']:
                response_text = f"Zatrzymano odtwarzanie utworu {result['paused_track']}"
            else:
                response_text = "Nie udało się zatrzymać odtwarzania. Sprawdź czy aplikacja Spotify jest aktywna."

            print(response_text)
            if voice_agent:
                voice_agent.speak(response_text)

            return result['success']

        elif parsed.get('action') == 'resume_playback':
            print("Wznawiam odtwarzanie...")
            if voice_agent:
                voice_agent.speak("Wznawiam odtwarzanie")

            result = resume_playback(access_token)

            if result['success']:
                response_text = f"Wznowiono odtwarzanie utworu {result['resumed_track']}"
            else:
                response_text = "Nie udało się wznowić odtwarzania. Sprawdź czy aplikacja Spotify jest aktywna."

            print(response_text)
            if voice_agent:
                voice_agent.speak(response_text)

            return result['success']

        elif parsed.get('action') == 'switch_device':
            device_type = parsed.get('device')
            if device_type:
                success = switch_device(access_token, device_type, voice_agent)

        elif parsed.get('action') == 'recommendation':
            print("Wyszukuję playlistę na podstawie nastroju...")
            if voice_agent:
                voice_agent.speak("Szukam odpowiedniej playlisty do Twojego nastroju.")

            # teraz uruchamiamy search_and_play_playlist
            mood_input = command  # jako mood_input dajemy cały oryginalny tekst użytkownika
            success = search_and_play_playlist(mood_input, access_token, voice_agent)

            return success

        elif parsed.get('action') == 'like':
            print("Polubianie aktualnego utworu...")

            result = like_current_song(access_token, voice_agent)

            if result['success']:
                if result['already_liked']:
                    response_text = f"Utwór {result['track_info']} jest już w Twoich ulubionych."
                else:
                    response_text = f"Dodano {result['track_info']} do polubionych utworów."
            else:
                response_text = "Nie udało się polubić aktualnego utworu."

            print(response_text)
            if voice_agent:
                voice_agent.speak(response_text)

            return result['success']

        elif parsed.get('action') == 'volume_up':
            print("Zwiększam głośność...")
            volume_change = int(parsed.get('volume', 10))
            if voice_agent:
                voice_agent.speak("Zwiększam głośność")

            result = set_volume(access_token, adjust_by=volume_change, voice_agent=voice_agent)
            return result['success']

        elif parsed.get('action') == 'volume_down':
            print("Zmniejszam głośność...")
            volume_change = int(parsed.get('volume', 10))
            if voice_agent:
                voice_agent.speak("Zmniejszam głośność")

            result = set_volume(access_token, adjust_by=-volume_change, voice_agent=voice_agent)
            return result['success']

        elif parsed.get('action') == 'set_volume':
            print("Ustawiam głośność...")
            volume_level = int(parsed.get('volume', 50))
            if voice_agent:
                voice_agent.speak(f"Ustawiam głośność na {volume_level} procent")

            result = set_volume(access_token, volume_level=volume_level, voice_agent=voice_agent)
            return result['success']

    except Exception as e:
        error_message = f"Wystąpił błąd: {str(e)}"
        print(error_message)
        import traceback
        traceback.print_exc()  # Dodaj pełny stack trace
        if voice_agent:
            voice_agent.speak("Przepraszam, wystąpił błąd podczas wykonywania komendy.")
        return False 