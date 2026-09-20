from flask import Flask, render_template
from datetime import datetime, timedelta
import requests, os

app = Flask(__name__)
API_KEY = os.getenv("API_FOOTBALL_KEY", "")

CONTINENT_MAP = {
    "England":"Europe","Spain":"Europe","Germany":"Europe","France":"Europe","Italy":"Europe",
    "Netherlands":"Europe","Portugal":"Europe","Belgium":"Europe","Scotland":"Europe","Turkey":"Europe",
    "South Africa":"Africa","South-Africa":"Africa","Egypt":"Africa","Botswana":"Africa","Morocco":"Africa","Nigeria":"Africa",
    "USA":"North America","Brazil":"South America","Argentina":"South America","Japan":"Asia","Saudi-Arabia":"Asia","Australia":"Oceania","World":"International"
}
def get_continent(c): return CONTINENT_MAP.get(c, "International")
def is_cup(n): return any(x in n.lower() for x in ["cup","copa","trophy","fa ","carabao"])
def is_amateur(n): return any(x in n.lower() for x in ["amateur","national league","conference","regional","non league"])

def get_league_extras(league_id, country):
    try:
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        t = requests.get("https://api-football-v1.p.rapidapi.com/v3/teams", headers=headers, params={"league": league_id, "season": 2024}, timeout=6).json()
        teams = [x["team"]["name"] for x in t.get("response", [])[:14]]
        s = requests.get("https://api-football-v1.p.rapidapi.com/v3/players/topscorers", headers=headers, params={"league": league_id, "season": 2024}, timeout=6).json()
        scorers = [{"name": p["player"]["name"], "goals": p["statistics"][0]["goals"]["total"]} for p in s.get("response", [])[:5]]
        if teams and scorers:
            return teams, scorers
    except:
        pass
    return [f"Team A - {country}", f"Team B - {country}"], [{"name":"Top Scorer","goals":8}]

def get_7_days_games():
    grouped = {}
    headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}

    # LOOP 7 DAYS
    for day_offset in range(7):
        date_obj = datetime.now() + timedelta(days=day_offset)
        date_str = date_obj.strftime("%Y-%m-%d")
        try:
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            data = requests.get(url, headers=headers, params={"date": date_str, "timezone": "Africa/Gaborone"}, timeout=10).json()
            for f in data.get("response", []):
                country = f["league"]["country"]
                lname = f["league"]["name"]
                lid = f["league"]["id"]
                cont = get_continent(country)
                ltype = "🏆 CUP" if is_cup(lname) else ("🌱 AMATEUR" if is_amateur(lname) else "🏟️ LEAGUE")
                key = f"{country}-{lname}"
                if cont not in grouped: grouped[cont] = {}
                if key not in grouped[cont]:
                    teams, scorers = get_league_extras(lid, country)
                    grouped[cont][key] = {"league": lname, "country": country, "type": ltype, "teams": teams, "scorers": scorers, "games": []}

                st = f["fixture"]["status"]["short"]
                grouped[cont][key]["games"].append({
                    "home": f["teams"]["home"]["name"],
                    "away": f["teams"]["away"]["name"],
                    "score": f"{f['goals']['home']}-{f['goals']['away']}" if f['goals']['home'] is not None else "vs",
                    "time": f"{date_str[5:]} {f['fixture']['date'][11:16]}",
                    "date": date_str,
                    "live": st in ["1H","2H","HT","LIVE"],
                    "finished": st in ["FT","AET","PEN"]
                })
        except Exception as e:
            print(f"Fail {date_str}: {e}")
            continue

    # Fallback dummy if API fails / no key
    if not grouped:
        grouped = {
            "Europe": {
                "Spain-LaLiga": {"league":"LaLiga","country":"Spain","type":"🏟️ LEAGUE","teams":["Barcelona","Real Madrid","Atletico"],"scorers":[{"name":"Lewandowski","goals":12}],"games":[
                    {"home":"Getafe","away":"Malaga","score":"1-0","time":"09-20 14:00","date":"2026-09-20","live":False,"finished":True},
                    {"home":"Atletico Madrid","away":"Real Madrid","score":"vs","time":"09-22 20:00","date":"2026-09-22","live":False,"finished":False}
                ]},
                "England-FA Cup": {"league":"FA Cup","country":"England","type":"🏆 CUP","teams":["Man City","Arsenal"],"scorers":[{"name":"Salah","goals":4}],"games":[
                    {"home":"Man City","away":"Arsenal","score":"vs","time":"09-24 19:45","date":"2026-09-24","live":False,"finished":False}
                ]},
            },
            "Africa": {
                "South Africa-PSL": {"league":"PSL","country":"South Africa","type":"🏟️ LEAGUE","teams":["Sundowns","Pirates","Chiefs"],"scorers":[{"name":"Shalulile","goals":8}],"games":[
                    {"home":"Sundowns","away":"Pirates","score":"vs","time":"09-21 19:00","date":"2026-09-21","live":False,"finished":False}
                ]}
            }
        }
    return grouped

@app.route("/")
def index():
    grouped = get_7_days_games()
    # count total games
    total = sum(len(l["games"]) for cont in grouped.values() for l in cont.values())
    return render_template("index.html", grouped_games=grouped, today=f"{datetime.now().strftime('%Y-%m-%d')} + 7 days ({total} games)")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
