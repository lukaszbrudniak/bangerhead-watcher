# === KONFIGURACJA ===
$env:BH_URL = "https://www.bangerhead.pl/curated-by-bangerhead-advent-calender-2025"

# --- E-MAIL (GMAIL, hasło aplikacji) ---
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"
$env:SMTP_USER = "arkadiusz.grema@gmail.com"
$env:SMTP_PASS = "qgmeoczidztxmkkg"
$env:EMAIL_FROM = "arkadiusz.grema@gmail.com"
$env:EMAIL_TO   = "lukasz.brudniak@gmail.com"

# === START SKRYPTU ===
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-Not (Test-Path $python)) { $python = "python" }
& $python (Join-Path $PSScriptRoot "watcher.py")
