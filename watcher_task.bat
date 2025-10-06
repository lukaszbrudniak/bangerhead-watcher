@echo off
set BH_URL=https://www.bangerhead.pl/curated-by-bangerhead-advent-calender-2025

REM --- E-MAIL (GMAIL haslo aplikacji) ---
set SMTP_HOST=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=arkadiusz.grema@gmail.com
set SMTP_PASS=qgmeoczidztxmkkg
set EMAIL_FROM=arkadiusz.grema@gmail.com
set EMAIL_TO=lukasz.brudniak@gmail.com

set BASE_DIR=%~dp0
set PY=%BASE_DIR%\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

cd /d "%BASE_DIR%"
"%PY%" "%BASE_DIR%\watcher.py" >> "%BASE_DIR%\watcher.log" 2>&1
