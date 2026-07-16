#!/usr/bin/env python3
"""
Flight Price Tracker
---------------------
Vérifie le prix d'un vol via l'API Google Flights de SerpApi pour plusieurs
combinaisons de dates de départ/retour, compare la meilleure offre avec
l'historique, et envoie un courriel de rapport listant les meilleures options.

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
OUTBOUND_DATES = os.environ.get("OUTBOUND_DATES", "2026-12-19,2026-12-20,2026-12-21").split(",")
RETURN_DATES = os.environ.get("RETURN_DATES", "2027-01-08,2027-01-09,2027-01-10,2027-01-11").split(",")
CURRENCY = os.environ.get("CURRENCY", "CAD")
TOP_N_PER_COMBO = 3

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD")
EMAIL_TO = os.environ.get("EMAIL_TO", EMAIL_ADDRESS)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

HISTORY_FILE = Path(__file__).parent / "price_history.json"


# ---------------------------------------------------------------------------
# 1. Récupérer les prix via SerpApi (Google Flights) pour chaque combinaison
#    de dates de départ/retour
# ---------------------------------------------------------------------------
def fetch_flights(outbound_date, return_date):
    params = {
        "engine": "google_flights",
        "departure_id": DEPARTURE_ID,
        "arrival_id": ARRIVAL_ID,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": CURRENCY,
        "hl": "fr",
        "type": "1",  # aller-retour
        "sort_by": "2",  # trier par prix (par défaut Google favorise les compagnies "préférées")
        "api_key": SERPAPI_KEY,
    }

    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    candidates = (data.get("best_flights") or []) + (data.get("other_flights") or [])
    options = [
        {"price": f["price"], "airline": f.get("flights", [{}])[0].get("airline", "?")}
        for f in candidates
        if isinstance(f.get("price"), (int, float))
    ]
    if not options:
        raise RuntimeError(f"Aucun prix trouvé dans la réponse SerpApi: {data.get('error', data)}")

    options.sort(key=lambda o: o["price"])
    return options


def fetch_all_combos():
    if not SERPAPI_KEY:
        print("ERREUR: SERPAPI_KEY manquant.", file=sys.stderr)
        sys.exit(1)

    combo_results = []
    for outbound_date in OUTBOUND_DATES:
        for return_date in RETURN_DATES:
            try:
                options = fetch_flights(outbound_date, return_date)
            except Exception as exc:
                print(f"AVERTISSEMENT: échec pour {outbound_date} → {return_date}: {exc}", file=sys.stderr)
                continue
            combo_results.append({
                "outbound_date": outbound_date,
                "return_date": return_date,
                "options": options[:TOP_N_PER_COMBO],
            })

    if not combo_results:
        raise RuntimeError("Aucune combinaison de dates n'a retourné de résultat.")

    combo_results.sort(key=lambda c: c["options"][0]["price"])
    return combo_results


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
def build_report(history, today_entry, combo_results):
    best = combo_results[0]
    best_option = best["options"][0]

    lines = [
        f"Vol {DEPARTURE_ID} → {ARRIVAL_ID}",
        "",
        f"MEILLEURE OFFRE : {best_option['price']} {CURRENCY} ({best_option['airline']})",
        f"  Dates : {best['outbound_date']} → {best['return_date']}",
    ]

    yesterday_price = history[-2]["price"] if len(history) >= 2 else None
    if yesterday_price is not None:
        diff = today_entry["price"] - yesterday_price
        if diff > 0:
            lines.append(f"  Variation depuis le dernier relevé : +{diff} {CURRENCY} (hausse)")
        elif diff < 0:
            lines.append(f"  Variation depuis le dernier relevé : {diff} {CURRENCY} (baisse) 🎉")
        else:
            lines.append("  Variation depuis le dernier relevé : aucun changement")

    last_7 = history[-7:]
    if len(last_7) >= 2:
        prices_7 = [h["price"] for h in last_7]
        lines += [
            "",
            f"Sur les {len(last_7)} derniers relevés :",
            f"  Min : {min(prices_7)} {CURRENCY}",
            f"  Max : {max(prices_7)} {CURRENCY}",
        ]

    lines += ["", "Détail par combinaison de dates (triées du moins cher au plus cher) :"]
    for combo in combo_results:
        lines.append(f"\n{combo['outbound_date']} → {combo['return_date']} :")
        for option in combo["options"]:
            lines.append(f"  - {option['price']} {CURRENCY} ({option['airline']})")

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
    combo_results = fetch_all_combos()
    best = combo_results[0]
    best_option = best["options"][0]

    history = load_history()
    today_entry = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "price": best_option["price"],
        "airline": best_option["airline"],
        "outbound_date": best["outbound_date"],
        "return_date": best["return_date"],
    }
    history.append(today_entry)
    save_history(history)

    report = build_report(history, today_entry, combo_results)
    print(report)  # utile pour les logs GitHub Actions

    subject = f"✈️ Vol {DEPARTURE_ID}-{ARRIVAL_ID} : à partir de {best_option['price']} {CURRENCY}"
    send_email(subject, report)


if __name__ == "__main__":
    main()
