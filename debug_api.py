#!/usr/bin/env python3
"""Script de diagnostic temporaire : dump brut de la réponse SerpApi pour un seul couple de dates."""

import json
import os

import requests

params = {
    "engine": "google_flights",
    "departure_id": "YQB",
    "arrival_id": "DSS",
    "outbound_date": "2026-12-19",
    "return_date": "2027-01-08",
    "currency": "CAD",
    "hl": "fr",
    "type": "1",
    "sort_by": "2",
    "api_key": os.environ["SERPAPI_KEY"],
}

resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
resp.raise_for_status()
data = resp.json()

best = data.get("best_flights") or []
other = data.get("other_flights") or []

print(f"best_flights: {len(best)} entrées")
print(f"other_flights: {len(other)} entrées")

all_entries = best + other
airlines = sorted({e.get("flights", [{}])[0].get("airline", "?") for e in all_entries})
print(f"Compagnies vues (leg 1 de chaque itinéraire) : {airlines}")

for label, group in [("best_flights", best), ("other_flights", other)]:
    print(f"\n--- {label} ---")
    for e in group:
        segs = e.get("flights", [])
        carriers = [s.get("airline") for s in segs]
        print(f"  prix={e.get('price')} type={e.get('type')} escales={len(segs)-1} compagnies_segments={carriers} departure_token_present={'departure_token' in e}")

print("\n--- price_insights ---")
print(json.dumps(data.get("price_insights"), ensure_ascii=False, indent=2))

print("\n--- erreur éventuelle ---")
print(data.get("error"))
