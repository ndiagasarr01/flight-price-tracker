#!/usr/bin/env python3
"""
Flight Price Tracker
---------------------
Vérifie quotidiennement le prix d'un vol via l'API Google Flights de SerpApi,
compare avec l'historique, et envoie un courriel de rapport.

Configuration : voir les variables d'environnement listées ci-dessous (README.md).
"""

import json
import os
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuration (modifiable ici ou via variables d'environnement)
# ---------------------------------------------------------------------------
DEPARTURE_ID = os.environ.get("DEPARTURE_ID", "YQB")   # Québec
ARRIVAL_ID = os.environ.get("ARRIVAL_ID", "DSS")        # Dakar (Blaise Diagne)
OUTBOUND_DATE = os.environ.get("OUTBOUND_DATE", "2026-12-19")
RETURN_DATE = os.environ.get("RETURN_DATE", "2027-01-08")
CURRENCY = os.environ.get("CURRENCY", "CAD")

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO", EMAIL_ADDRESS)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

HISTORY_FILE = Path(__file__).parent / "price_history.json"


# ---------------------------------------------------------------------------
# 1. Récupérer le prix actuel via SerpApi (Google Flights)
# ---------------------------------------------------------------------------
def fetch_current_price():
    if not SERPAPI_KEY:
        print("ERREUR: SERPAPI_KEY manquant.", file=sys.stderr)
        sys.exit(1)

    params = {
        "engine": "google_flights",
        "departure_id": DEPARTURE_ID,
        "arrival_id": ARRIVAL_ID,
        "outbound_date": OUTBOUND_DATE,
        "return_date": RETURN_DATE,
        "currency": CURRENCY,
        "hl": "fr",
        "type": "1",  # aller-retour
        "api_key": SERPAPI_KEY,
    }

    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    candidates = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    prices = [f["price"] for f in candidates if isinstance(f.get("price"), (int, float))]

    if not prices:
        raise RuntimeError(f"Aucun prix trouvé dans la réponse SerpApi: {data.get('error', data)}")

    cheapest = min(prices)
    airline = next(
        (f.get("flights", [{}])[0].get("airline", "?") for f in candidates if f.get("price") == cheapest),
        "?",
    )
    return cheapest, airline


# ---------------------------------------------------------------------------
# 2. Charger / mettre à jour l'historique local
# ---------------------------------------------------------------------------
def load_history():
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# 3. Construire et envoyer le courriel de rapport
# ---------------------------------------------------------------------------
def build_report(history, today_entry):
    price_today = today_entry["price"]
    yesterday_price = history[-2]["price"] if len(history) >= 2 else None

    lines = [
        f"Vol {DEPARTURE_ID} → {ARRIVAL_ID}",
        f"Dates : {OUTBOUND_DATE} → {RETURN_DATE}",
        "",
        f"Prix aujourd'hui : {price_today} {CURRENCY} ({today_entry['airline']})",
    ]

    if yesterday_price is not None:
        diff = price_today - yesterday_price
        if diff > 0:
            lines.append(f"Variation depuis hier : +{diff} {CURRENCY} (hausse)")
        elif diff < 0:
            lines.append(f"Variation depuis hier : {diff} {CURRENCY} (baisse) 🎉")
        else:
            lines.append("Variation depuis hier : aucun changement")

    last_7 = history[-7:]
    if len(last_7) >= 2:
        prices_7 = [h["price"] for h in last_7]
        lines += [
            "",
            f"Sur les {len(last_7)} derniers relevés :",
            f"  Min : {min(prices_7)} {CURRENCY}",
            f"  Max : {max(prices_7)} {CURRENCY}",
        ]

    lines += ["", f"(Relevé du {today_entry['date']})"]
    return "\n".join(lines)


def send_email(subject, body):
    if not (EMAIL_ADDRESS and EMAIL_APP_PASSWORD and EMAIL_TO):
        print("ERREUR: variables EMAIL_ADDRESS / EMAIL_APP_PASSWORD / EMAIL_TO manquantes.", file=sys.stderr)
        sys.exit(1)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_TO

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, [EMAIL_TO], msg.as_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    price, airline = fetch_current_price()

    history = load_history()
    today_entry = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "price": price,
        "airline": airline,
    }
    history.append(today_entry)
    save_history(history)

    report = build_report(history, today_entry)
    print(report)  # utile pour les logs GitHub Actions

    subject = f"✈️ Vol {DEPARTURE_ID}-{ARRIVAL_ID} : {price} {CURRENCY}"
    send_email(subject, report)


if __name__ == "__main__":
    main()
