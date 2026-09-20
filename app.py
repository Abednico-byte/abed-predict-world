from flask import Flask, render_template
from datetime import datetime, timedelta
import requests, os

app = Flask(__name__)
API_KEY = os.getenv("API_FOOTBALL_KEY", "")

CONTINENT_MAP = {
    "England":"Europe","Spain":"Europe","Germany":"Europe","France":"Europe","Italy":"Europe","Netherlands":"Europe","Portugal":"Europe","Belgium":"Europe","Scotland":"Europe","Turkey":"Europe",
    "South Africa":"Africa","South-Africa":"Africa","Egypt":"Africa","Botswana":"Africa","Morocco":"Africa",
    "USA":"North America","Brazil":"South America","Argentina":"South America","Japan":"Asia","Saudi-Arabia":"Asia","Australia":"Oceania","World":"International"
}
def get_continent(c): return CONTINENT_MAP.get(c, "International")
def is_cup(n): return any(x in n.lower() for x in ["cup","copa","trophy","fa "])
def is_amateur(n): return any(x in n.lower() for x in ["amateur","national league","conference","regional"])

@app.route("/")
def index():
    grouped = {}
    try:
        headers = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"} if API_KEY else {}
        # 7 DAYS LOOP - only 7 calls total
        for offset in range(7):
            d = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%d")
            try:
                if not API_KEY:
                    raise Exception("no key - use dummy")
                r = requests.get("https://api-football-v1.p.rapidapi.com/v3/fixtures", headers=headers, params={"date": d}, timeout=8).json()
                for f in r.get("response", []):
                    country = f["league"]["country"]
                    lname = f["league"]["name"]
                    cont = get_continent(country)
                    key = f"{country}-{lname}"
                    ltype = "🏆 CUP" if is_cup(lname) else ("🌱 AMATEUR" if is_amateur(lname) else "🏟️ LEAGUE")
                    if cont not in grouped: grouped[cont] = {}
                    if key not in grouped[cont]:
                        grouped[cont][key] = {
                            "league": lname, "country": country, "type": ltype,
                            "teams": [f["teams"]["home"]["name"], f["teams"]["away"]["name"]],
                            "scorers": [{"name":"Top Scorer","goals":9}],
                            "games": []
                        }
                    # add team to list
                    if f["teams"]["home"]["name"] not in grouped[cont][key]["teams"]:
                        grouped[cont][key]["teams"].append(f["teams"]["home"]["name"])
                    if f["teams"]["away"]["name"] not in grouped[cont][key]["teams"]:
                        grouped[cont][key]["teams"].append(f["teams"]["away"]["name"])

                    st = f["fixture"]["status"]["short"]
                    grouped[cont][key]["games"].append({
                        "home": f["teams"]["home"]["name"],
                        "away": f["teams"]["away"]["name"],
                        "score": f"{f['goals']['home']}-{f['goals']['away']}" if f['goals']['home'] is not None else "vs",
                        "time": f"{d[5:]} {f['fixture']['date'][11:16]}",
                        "live": st in ["1H","2H","HT","LIVE"],
                        "finished": st in ["FT","AET","PEN"]
                    })
            except:
                continue
    except Exception as e:
        print(e)

    # Fallback if no API or no games
    if not grouped:
        grouped = {
            "Europe": {
                "Spain-LaLiga": {"league":"LaLiga","country":"Spain","type":"🏟️ LEAGUE","teams":["Barcelona","Real Madrid","Atletico","Getafe","Malaga"],"scorers":[{"name":"Lewandowski","goals":12},{"name":"Mbappe","goals":10}],"games":[
                    {"home":"Getafe","away":"Malaga","score":"1-0","time":"09-20 14:00","live":False,"finished":True},
                    {"home":"Atletico Madrid","away":"Real Madrid","score":"vs","time":"09-22 20:00","live":False,"finished":False},
                    {"home":"Barcelona","away":"Sevilla","score":"vs","time":"09-24 18:30","live":False,"finished":False}
                ]},
                "England-FA Cup": {"league":"FA Cup","country":"England","type":"🏆 CUP","teams":["Man City","Arsenal","Liverpool"],"scorers":[{"name":"Salah","goals":4}],"games":[
                    {"home":"Man City","away":"Arsenal","score":"vs","time":"09-24 19:45","live":False,"finished":False}
                ]}
            },
            "Africa": {
                "South Africa-PSL": {"league":"PSL","country":"South Africa","type":"🏟️ LEAGUE","teams":["Sundowns","Pirates","Chiefs"],"scorers":[{"name":"Shalulile","goals":8}],"games":[
                    {"home":"Sundowns","away":"Pirates","score":"vs","time":"09-21 19:00","live":False,"finished":False}
                ]}
            }
        }

    total = sum(len(l["games"]) for cont in grouped.values() for l in cont.values())
    return render_template("index.html", grouped_games=grouped, today=f"{datetime.now().strftime('%Y-%m-%d')} + 7 days ({total} games)")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
