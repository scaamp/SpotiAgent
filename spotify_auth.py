import json
import os
import threading
import time
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys and settings from environment variables
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
TOKEN_FILE = "spotify_tokens.json"
auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code

        # Wyciągnięcie i zapisanie kodu autoryzacji z URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if 'code' in params:
            auth_code = params['code'][0]

            # Wysłanie odpowiedzi sukcesu do przeglądarki
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(
                "<html><body><h1>Autoryzacja zakończona sukcesem!</h1><p>Możesz zamknąć to okno.</p></body></html>",
                "utf-8"))
        else:
            # Wysłanie odpowiedzi błędu
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(
                bytes("<html><body><h1>Autoryzacja nie powiodła się!</h1><p>Nie otrzymano kodu.</p></body></html>",
                      "utf-8"))

def save_tokens(token_data):
    """Zapisuje tokeny do pliku"""
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f)
    print(f"Tokeny zapisane do {TOKEN_FILE}")

def load_tokens():
    """Ładuje tokeny z pliku"""
    if not os.path.exists(TOKEN_FILE):
        return None

    try:
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def refresh_access_token(refresh_token):
    """Odświeża token dostępu przy użyciu tokena odświeżania"""
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        print(f"Błąd odświeżania tokena: {response.status_code}")
        print(response.text)
        return None

    token_data = response.json()

    # Spotify nie zawsze zwraca nowy refresh_token, więc zachowujemy stary
    if 'refresh_token' not in token_data:
        token_data['refresh_token'] = refresh_token

    # Zapisz nowe dane tokena
    save_tokens(token_data)

    return token_data.get("access_token")

def get_auth_code():
    """Uruchamia lokalny serwer i otwiera stronę autoryzacji Spotify, aby automatycznie uzyskać kod"""
    global auth_code
    auth_code = None

    # Uruchom lokalny serwer w osobnym wątku
    server_address = ('', 8888)
    httpd = HTTPServer(server_address, CallbackHandler)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Wygeneruj URL autoryzacji ze wszystkimi wymaganymi zakresami
    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
        f"&scope=user-read-playback-state%20user-modify-playback-state%20user-library-modify%20user-library-read"
    )

    # Otwórz przeglądarkę dla użytkownika w celu autoryzacji
    print(f"Otwieram przeglądarkę do autoryzacji (tylko za pierwszym razem)...")
    webbrowser.open(auth_url)

    # Poczekaj na przetworzenie callbacku
    timeout = 120  # sekund
    start_time = time.time()

    while auth_code is None and time.time() - start_time < timeout:
        time.sleep(0.5)

    # Zatrzymaj serwer
    httpd.shutdown()
    server_thread.join(1)

    if auth_code:
        print("Kod autoryzacyjny otrzymany pomyślnie!")
        return auth_code
    else:
        print("Nie udało się otrzymać kodu autoryzacyjnego w czasie oczekiwania.")
        return None

def get_token():
    """Pobiera token dostępu, najpierw próbując odświeżyć istniejący, a jeśli to się nie uda, uzyskuje nowy"""
    # Najpierw sprawdź, czy mamy zapisane tokeny
    token_data = load_tokens()

    # Jeśli mamy zapisany token odświeżania, spróbuj go użyć
    if token_data and 'refresh_token' in token_data:
        print("Znaleziono zapisany token odświeżania. Próbuję odświeżyć token dostępu...")
        access_token = refresh_access_token(token_data['refresh_token'])
        if access_token:
            return access_token

    # Jeśli nie mamy tokena odświeżania lub odświeżenie nie powiodło się, uzyskaj nowy kod autoryzacji
    print("Potrzebna nowa autoryzacja...")
    code = get_auth_code()

    if not code:
        raise Exception("Nie udało się uzyskać kodu autoryzacji")

    # Wymień kod na token dostępu
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        print(f"Błąd uzyskiwania tokena: {response.status_code}")
        print(response.text)
        return None

    token_data = response.json()
    print("Odpowiedź z tokenem:", token_data)

    # Zapisz tokeny do pliku do późniejszego użycia
    save_tokens(token_data)

    return token_data.get("access_token") 