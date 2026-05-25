"""
fetch_data.py — Ganga Daily Intelligence Updater
Runs via GitHub Actions every day at 06:00 IST.
Sources: Open-Meteo (free, no API key), emem.dev
Output: data.json (read by index.html at page load)
"""

import json, requests
from datetime import datetime, timezone, timedelta

IST     = timezone(timedelta(hours=5, minutes=30))
NOW     = datetime.now(IST)
HEADERS = {"User-Agent": "ProjectBanana-GangaDashboard/1.0 (github.com/SHIVANASH1/Ganga)"}

STATIONS = [
    {"id":"gangotri",   "name":"Gaumukh / Gangotri",  "state":"Uttarakhand",  "lat":30.92,"lng":79.07,"km":0,   "bod_base":0.5},
    {"id":"uttarkashi", "name":"Uttarkashi",           "state":"Uttarakhand",  "lat":30.72,"lng":78.43,"km":85,  "bod_base":1.2},
    {"id":"devprayag",  "name":"Devprayag",            "state":"Uttarakhand",  "lat":30.15,"lng":78.61,"km":216, "bod_base":1.8},
    {"id":"rishikesh",  "name":"Rishikesh",            "state":"Uttarakhand",  "lat":30.09,"lng":78.27,"km":249, "bod_base":2.5},
    {"id":"haridwar",   "name":"Haridwar",             "state":"Uttarakhand",  "lat":29.96,"lng":78.16,"km":253, "bod_base":3.1},
    {"id":"bijnor",     "name":"Bijnor",               "state":"Uttar Pradesh","lat":29.37,"lng":78.13,"km":330, "bod_base":4.5},
    {"id":"narora",     "name":"Narora",               "state":"Uttar Pradesh","lat":28.19,"lng":78.40,"km":450, "bod_base":5.8},
    {"id":"kanpur",     "name":"Kanpur",               "state":"Uttar Pradesh","lat":26.45,"lng":80.35,"km":680, "bod_base":38.4},
    {"id":"prayagraj",  "name":"Prayagraj",            "state":"Uttar Pradesh","lat":25.44,"lng":81.84,"km":780, "bod_base":17.2},
    {"id":"varanasi",   "name":"Varanasi",             "state":"Uttar Pradesh","lat":25.32,"lng":83.00,"km":845, "bod_base":24.6},
    {"id":"ghazipur",   "name":"Ghazipur",             "state":"Uttar Pradesh","lat":25.58,"lng":83.58,"km":900, "bod_base":14.5},
    {"id":"buxar",      "name":"Buxar",                "state":"Bihar",        "lat":25.57,"lng":83.98,"km":940, "bod_base":10.8},
    {"id":"patna",      "name":"Patna",                "state":"Bihar",        "lat":25.60,"lng":85.14,"km":1027,"bod_base":12.4},
    {"id":"munger",     "name":"Munger",               "state":"Bihar",        "lat":25.37,"lng":86.47,"km":1100,"bod_base":9.4},
    {"id":"bhagalpur",  "name":"Bhagalpur",            "state":"Bihar",        "lat":25.25,"lng":87.00,"km":1200,"bod_base":7.6},
    {"id":"farakka",    "name":"Farakka Barrage",      "state":"West Bengal",  "lat":24.82,"lng":87.93,"km":1500,"bod_base":6.8},
    {"id":"murshidabad","name":"Murshidabad",          "state":"West Bengal",  "lat":24.18,"lng":88.27,"km":1560,"bod_base":7.2},
    {"id":"kolkata",    "name":"Kolkata (Hooghly)",    "state":"West Bengal",  "lat":22.57,"lng":88.36,"km":2350,"bod_base":18.4},
    {"id":"sagar",      "name":"Sagar Island",         "state":"West Bengal",  "lat":21.65,"lng":88.05,"km":2525,"bod_base":8.5},
]

def fetch_weather(lat, lng):
    url = (f"https://api.open-meteo.com/v1/forecast"
           f"?latitude={lat}&longitude={lng}"
           f"&current=temperature_2m,precipitation,river_discharge"
           f"&timezone=Asia%2FKolkata&forecast_days=1")
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        r.raise_for_status()
        cur = r.json().get("current", {})
        return {
            "temp_c":          round(cur.get("temperature_2m", 0), 1),
            "precip_mm":       round(cur.get("precipitation",  0), 1),
            "river_discharge": round(cur.get("river_discharge",0), 0),
        }
    except Exception as e:
        print(f"    ⚠ weather: {e}")
        return {"temp_c": None, "precip_mm": None, "river_discharge": None}

def fetch_air(lat, lng):
    url = (f"https://air-quality-api.open-meteo.com/v1/air-quality"
           f"?latitude={lat}&longitude={lng}"
           f"&current=pm2_5,pm10,nitrogen_dioxide")
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        r.raise_for_status()
        cur = r.json().get("current", {})
        return {
            "pm25": round(cur.get("pm2_5", 0), 1),
            "pm10": round(cur.get("pm10",  0), 1),
            "no2":  round(cur.get("nitrogen_dioxide", 0), 1),
        }
    except Exception as e:
        print(f"    ⚠ air: {e}")
        return {"pm25": None, "pm10": None, "no2": None}

def estimate_bod(base, precip, temp):
    f = 1.0
    if precip:
        if   precip > 10: f += 0.20
        elif precip > 3:  f += 0.10
    if temp:
        if   temp > 35:   f += 0.10
        elif temp < 15:   f -= 0.05
    return round(base * f, 2)

def flood_alert(precip, km):
    zones = [(580,720,"Kanpur"),(750,870,"Prayagraj-Varanasi"),
             (920,1100,"Buxar-Patna"),(1150,1320,"Bihar-Kosi")]
    if precip and precip > 20:
        for a,b,name in zones:
            if a <= km <= b:
                return f"⚠ FLOOD WATCH — {name}"
    return "Normal"

def main():
    print(f"\n🌊 Ganga Updater — {NOW.strftime('%Y-%m-%d %H:%M IST')}\n")
    results = []
    for s in STATIONS:
        print(f"  📍 {s['name']}")
        w = fetch_weather(s["lat"], s["lng"])
        a = fetch_air(s["lat"], s["lng"])
        bod = estimate_bod(s["bod_base"], w["precip_mm"], w["temp_c"])
        results.append({**s,
            "temp_c": w["temp_c"], "precip_mm": w["precip_mm"],
            "river_discharge": w["river_discharge"],
            "pm25": a["pm25"], "pm10": a["pm10"], "no2": a["no2"],
            "bod_today": bod, "flood_alert": flood_alert(w["precip_mm"], s["km"]),
        })

    out = {
        "last_updated":     NOW.strftime("%Y-%m-%d %H:%M IST"),
        "last_updated_iso": NOW.isoformat(),
        "source":           "Open-Meteo · emem.dev · CPCB baseline",
        "stations":         results,
    }
    with open("data.json","w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n✅ data.json — {len(results)} stations done.\n")

if __name__ == "__main__":
    main()
