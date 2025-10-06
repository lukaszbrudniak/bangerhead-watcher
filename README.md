# Bangerhead – watcher dostępności

Ten prosty skrypt sprawdza, czy produkt na stronie Bangerhead jest dostępny, i wysyła powiadomienie (Telegram i/lub e‑mail), gdy status zmieni się na **in stock**.

## 1) Instalacja
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Konfiguracja
Ustaw zmienne środowiskowe (np. w pliku `.env` lub bezpośrednio w cronie):

Wymagane (adres strony możesz podmienić na inny produkt):
```
BH_URL="https://www.bangerhead.pl/curated-by-bangerhead-advent-calender-2025"
```

Opcjonalne – Telegram (polecam, bardzo proste):
```
TG_BOT_TOKEN="123456:ABC-DEF..."   # utwórz bota w @BotFather
TG_CHAT_ID="123456789"             # swój chat_id; sprawdzisz np. przez @RawDataBot
```

Opcjonalne – e‑mail (SMTP):
```
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
SMTP_USER="twoj_login@gmail.com"
SMTP_PASS="haslo_aplikacji"        # w Gmailu użyj "hasła aplikacji"
EMAIL_FROM="twoj_login@gmail.com"
EMAIL_TO="adres_docelowy@example.com"
```

## 3) Uruchomienie
```bash
export BH_URL="https://www.bangerhead.pl/curated-by-bangerhead-advent-calender-2025"
python watcher.py
```

Wyjście zakończy się kodem:
- `0` — dostępny **lub** status niejednoznaczny (żeby cron nie traktował jako błąd),
- `1` — niedostępny,
- `2` — błąd pobierania.

Skrypt zapisuje ostatni status w `last_status.json`, żeby nie wysyłać powiadomień wielokrotnie.

## 4) Automatyczne sprawdzanie (cron)
Otwórz crontab:
```bash
crontab -e
```
Dodaj np. sprawdzanie co 30 min (w lokalnej strefie):
```
*/30 * * * * cd /ścieżka/do/bangerhead_scraper && /ścieżka/do/python .venv/bin/python watcher.py >> cron.log 2>&1
```

Jeśli konfigurację trzymasz w `.env`, możesz dodać na górze crona:
```
SHELL=/bin/bash
BASH_ENV=/ścieżka/do/bangerhead_scraper/.env
```

## 5) Windows – Harmonogram zadań
Stwórz zadanie uruchamiające:
```
C:\ścieżka\do\python.exe C:\ścieżka\do\bangerhead_scraper\watcher.py
```
ustaw częstotliwość (np. co godzinę).

## 6) Wskazówki
- Nie ustawiaj interwału krótszego niż 5–10 min, żeby nie przeciążać serwisu.
- Skrypt sprawdza zarówno dane `schema.org` (JSON‑LD), jak i teksty na stronie (np. „Wyprzedane”, „Do koszyka”).
- W razie problemów odpal z `export STATE_FILE=/pełna/ścieżka/last_status.json` i sprawdź `cron.log`.
