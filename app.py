from flask import Flask, render_template
from datetime import datetime, timedelta
import requests, os

app = Flask(__name__)
API_KEY = os.getenv("API_FOOTBALL_KEY", "")

CONTINENT_MAP = {"England":"Europe","Spain":"Europe","Germany":"Europe","France":"Europe","Italy":"Europe","Netherlands":"Europe","Portugal":"Europe","Belgium":"Europe","Scotland":"Europe","Turkey":"Europe","South Africa":"Africa","Egypt":"Africa","Botswana":"Africa","Morocco":"Africa","USA":"North America","Brazil":"South America","Argentina":"South America","Japan":"Asia","Saudi-Arabia":"Asia","Australia":"Oceania","World":"International"}
def get_continent(c): return CONTINENT_MAP.get(c, "International")
def is_cup(n): return any(x in n.lower() for x in ["cup","copa","fa ","trophy"])
def is_amateur(n): return any(x in n.lower() for x in ["amateur","national","conference","regional","u19","u21"])

@app.route("/")
def index():
    grouped = {}
    try:
        if API_KEY:
            headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}
            for i in range(7):
                d = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
                try:
                    r = requests.get("https://api-football-v1.p.rapidapi.com/v3/fixtures", headers=headers, params={"date": d}, timeout=6).json()
                    for f in r.get("response", []):
                        country = f["league"]["country"]; lname = f["league"]["name"]; cont = get_continent(country); key = f"{country}-{lname}"
                        if cont not in grouped: grouped[cont] = {}
                        if key not in grouped[cont]:
                            ltype = "🏆 CUP" if is_cup(lname) else ("🌱 AMATEUR" if is_amateur(lname) else "🏟️ LEAGUE")
                            grouped[cont][key] = {"league": lname, "country": country, "type": ltype, "teams": [], "scorers": [{"name":"Loading...","goals":0}], "games": []}
                        for tm in [f["teams"]["home"]["name"], f["teams"]["away"]["name"]]:
                            if tm not in grouped[cont][key]["teams"]: grouped[cont][key]["teams"].append(tm)
                        st = f["fixture"]["status"]["short"]
                        grouped[cont][key]["games"].append({"home": f["teams"]["home"]["name"], "away": f["teams"]["away"]["name"], "score": f"{f['goals']['home']}-{f['goals']['away']}" if f['goals']['home'] is not None else "vs", "time": f"{d[5:]} {f['fixture']['date'][11:16]}", "live": st in ["1H","2H","HT","LIVE"], "finished": st in ["FT","AET","PEN"]})
                except: continue
    except: pass

    if not grouped:
        grouped = {"Europe":{"Spain-LaLiga":{"league":"LaLiga","country":"Spain","type":"🏟️ LEAGUE","teams":["Barcelona","Real Madrid","Atletico","Getafe","Malaga"],"scorers":[{"name":"Lewandowski","goals":12}],"games":[{"home":"Getafe","away":"Malaga","score":"1-0","time":"09-20 14:00","live":False,"finished":True},{"home":"Atletico","away":"Real Madrid","score":"vs","time":"09-22 20:00","live":False,"finished":False}]}},"Africa":{"South Africa-PSL":{"league":"PSL","country":"South Africa","type":"🏟️ LEAGUE","teams":["Sundowns","Pirates","Chiefs"],"scorers":[{"name":"Shalulile","goals":8}],"games":[{"home":"Sundowns","away":"Pirates","score":"vs","time":"09-21 19:00","live":False,"finished":False}]}}}

    total = sum(len(l["games"]) for c in grouped.values() for l in c.values())
    return render_template("index.html", grouped_games=grouped, today=f"{datetime.now().strftime('%Y-%m-%d')} +7d ({total} games)")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
