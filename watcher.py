#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bangerhead availability watcher
- Checks availability of a product page.
- Notifies via Telegram and/or email when status turns to IN STOCK.
- Saves last seen status to avoid duplicate alerts.
"""

import os
import re
import sys
import json
import time
import smtplib
import logging
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup

URL = os.getenv("BH_URL", "https://www.bangerhead.pl/curated-by-bangerhead-advent-calender-2025")
STATE_FILE = os.getenv("STATE_FILE", "last_status.json")
TIMEOUT = int(os.getenv("TIMEOUT", "20"))

# --- Notifications (configure via env vars) ---
# Telegram (optional)
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")  # e.g. 123456:ABC-DEF...
TG_CHAT_ID = os.getenv("TG_CHAT_ID")      # e.g. 123456789

# Email (optional)
SMTP_HOST = os.getenv("SMTP_HOST")        # e.g. smtp.gmail.com
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")          # destination address
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl,en;q=0.9",
}

KEYWORDS_OUT = [
    "wyprzedany", "wyprzedane", "wyprzedana",
    "niedostępny", "niedostępne",
    "brak w magazynie",
    "sold out", "out of stock",
]
KEYWORDS_IN = [
    "dostępny", "dostępne", "na stanie",
    "in stock", "add to cart", "do koszyka", "kup teraz"
]

def load_last_status(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f).get("status")
    except Exception:
        return None

def save_last_status(path: str, status: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"status": status, "ts": int(time.time())}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning("Nie udało się zapisać statusu: %s", e)

def normalize_text(txt: str) -> str:
    return re.sub(r"\s+", " ", txt).strip().lower()

def parse_jsonld_availability(soup: BeautifulSoup) -> Optional[str]:
    # Look for schema.org offers with availability InStock/OutOfStock
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        # Make it iterable of dicts
        candidates = []
        if isinstance(data, dict):
            candidates = [data]
        elif isinstance(data, list):
            candidates = data
        else:
            continue
        for node in candidates:
            offers = node.get("offers")
            if not offers:
                continue
            if isinstance(offers, dict):
                offers = [offers]
            for offer in offers:
                avail = offer.get("availability") or offer.get("availabilityStarts")
                if isinstance(avail, str):
                    al = avail.lower()
                    if "instock" in al:
                        return "in_stock"
                    if "outofstock" in al or "oos" in al:
                        return "out_of_stock"
    return None

def heuristic_availability(soup: BeautifulSoup) -> Tuple[str, str]:
    """Return ('in_stock'|'out_of_stock'|'unknown', reason_text)"""
    text = normalize_text(soup.get_text(" "))
    # Strong hints
    for kw in KEYWORDS_OUT:
        if kw in text:
            return "out_of_stock", f"Znaleziono słowo kluczowe: '{kw}'"
    for kw in KEYWORDS_IN:
        if kw in text:
            return "in_stock", f"Znaleziono słowo kluczowe: '{kw}'"

    # Buttons / add-to-cart controls
    for btn in soup.find_all(["button", "a", "input"]):
        bt = normalize_text(btn.get_text(" ") or btn.get("value", ""))
        if not bt:
            continue
        if any(kw in bt for kw in KEYWORDS_IN):
            return "in_stock", f"Przycisk: '{bt}'"
        if any(kw in bt for kw in KEYWORDS_OUT):
            return "out_of_stock", f"Przycisk: '{bt}'"
    return "unknown", "Brak jednoznacznych wskaźników"

def fetch_page(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

def notify_telegram(msg: str) -> None:
    if not (TG_BOT_TOKEN and TG_CHAT_ID):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": msg, "disable_web_page_preview": True},
            timeout=15,
        )
    except Exception as e:
        logging.warning("Telegram błąd: %s", e)

def notify_email(subject: str, body: str) -> None:
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO and EMAIL_FROM):
        return
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Date"] = formatdate(localtime=True)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
    except Exception as e:
        logging.warning("E-mail błąd: %s", e)

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("Sprawdzam: %s", URL)

    try:
        soup = fetch_page(URL)
    except Exception as e:
        logging.error("Błąd pobierania strony: %s", e)
        return 2

    # 1) Try schema.org
    jsonld_status = parse_jsonld_availability(soup)
    if jsonld_status:
        status, reason = jsonld_status, "Dane schema.org"
    else:
        status, reason = heuristic_availability(soup)

    last = load_last_status(STATE_FILE)

    logging.info("Status: %s (%s). Poprzedni: %s", status, reason, last)

    # Only notify on transitions to in_stock
    if status == "in_stock" and last != "in_stock":
        title = "🎉 Bangerhead: produkt DOSTĘPNY!"
        body = f"Produkt jest dostępny: {URL}\n\nŹródło: {reason}"
        notify_telegram(f"{title}\n{URL}")
        notify_email(title, body)
        logging.info("Wysłano powiadomienia.")
    elif status == "out_of_stock":
        logging.info("Produkt niedostępny.")
    else:
        logging.info("Status niejednoznaczny.")

    save_last_status(STATE_FILE, status)
    # Exit codes: 0 ok, 1 oos, 2 error
    return 0 if status == "in_stock" else (1 if status == "out_of_stock" else 0)

if __name__ == "__main__":
    sys.exit(main())
