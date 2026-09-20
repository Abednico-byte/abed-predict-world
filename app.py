from flask import Flask, render_template
from datetime import datetime
import requests, os

app = Flask(__name__)
API_KEY = os.getenv("API_FOOTBALL_KEY", "")

CONTINENT_MAP = {
    "England":"Europe","Spain":"Europe","Germany":"Europe","France":"Europe","Italy":"Europe",
    "Netherlands":"Europe","Portugal":"Europe","Belgium":"Europe","Scotland":"Europe",
    "Wales":"Europe","Ireland":"Europe","Poland":"Europe","Sweden":"Europe",
    "South Africa":"Africa","South-Africa":"Africa","Egypt":"Africa","Botswana":"Africa",
    "Morocco":"Africa","Nigeria":"Africa","USA":"North America","Brazil":"South America",
    "Argentina":"South America","Japan":"Asia","Saudi-Arabia":"Asia","Australia":"Oceania","World":"International"
}
def get_continent(c): return CONTINENT_MAP.get(c, "Europe")

def is_cup(name):
    n = name.lower()
    return any(x in n for x in ["cup","copa","trophy","fa ","carabao","efl","dfb","knockout","play-off"])

def is_amateur(name):
    n = name.lower()
    return any(x in n for x in ["amateur","national league","isthmian","conference","regional","division 2","third","fourth","upl","non league"])

def get_league_extras(league_id, country):
    try:
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        t = requests.get("https://api-football-v1.p.rapidapi.com/v3/teams", headers=headers, params={"league": league_id, "season": 2024}, timeout=8).json()
        teams = [x["team"]["name"] for x in t.get("response", [])[:14]]
        s = requests.get("https://api-football-v1.p.rapidapi.com/v3/players/topscorers", headers=headers, params={"league": league_id, "season": 2024}, timeout=8).json()
        scorers = [{"name": p["player"]["name"], "goals": p["statistics"][0]["goals"]["total"]} for p in s.get("response", [])[:5]]
        return teams, scorers
    except:
        return ["Team A","Team B","Team C","Team D"], [{"name":"Top Scorer","goals":8}]

def get_all_games():
    grouped = {}
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}
        data = requests.get("https://api-football-v1.p.rapidapi.com/v3/fixtures", headers=headers, params={"date": today, "timezone": "Africa/Gaborone"}, timeout=12).json()
        for f in data.get("response", [])[:100]: # increased to 100 to include amateur + cups
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
                "home": f["teams"]["home"]["name"], "away": f["teams"]["away"]["name"],
                "score": f"{f['goals']['home']}-{f['goals']['away']}" if f['goals']['home'] is not None else "vs",
                "time": f["fixture"]["date"][11:16], "live": st in ["1H","2H","HT","LIVE"] and st not in ["FT"], "finished": st in ["FT","AET","PEN"]
            })
    except Exception as e:
        print(e)
    if not grouped:
        grouped = {
            "Europe": {
                "England-Premier League": {"league":"Premier League","country":"England","type":"🏟️ LEAGUE","teams":["Arsenal","Liverpool"],"scorers":[{"name":"Haaland","goals":15}],"games":[{"home":"Arsenal","away":"Liverpool","score":"vs","time":"18:30","live":False,"finished":False}]},
                "England-FA Cup": {"league":"FA Cup","country":"England","type":"🏆 CUP","teams":["Man City","Man United","Liverpool"],"scorers":[{"name":"Salah","goals":4}],"games":[{"home":"Man City","away":"Arsenal","score":"vs","time":"20:00","live":False,"finished":False}]},
                "England-National League": {"league":"National League - Amateur","country":"England","type":"🌱 AMATEUR","teams":["Wrexham","Chesterfield"],"scorers":[{"name":"Mullin","goals":10}],"games":[{"home":"Wrexham","away":"Notts County","score":"vs","time":"19:45","live":False,"finished":False}]},
            },
            "Africa": {"South Africa-PSL": {"league":"PSL","country":"South Africa","type":"🏟️ LEAGUE","teams":["Sundowns","Pirates"],"scorers":[{"name":"Shalulile","goals":8}],"games":[{"home":"Sundowns","away":"Pirates","score":"vs","time":"19:00","live":False,"finished":False}]}}
        }
    return grouped

@app.route("/")
def index():
    grouped = get_all_games()
    return render_template("index.html", grouped_games=grouped, today=datetime.now().strftime("%Y-%m-%d"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
