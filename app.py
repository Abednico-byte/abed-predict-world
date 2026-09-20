from flask import Flask, render_template
from datetime import datetime
import requests, os

app = Flask(__name__)
API_KEY = os.getenv("API_FOOTBALL_KEY", "YOUR_KEY_HERE")

def get_today_games_live():
    games = []
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        params = {"date": today, "timezone": "Africa/Gaborone"}
        data = requests.get(url, headers=headers, params=params, timeout=10).json()
        for f in data.get("response", [])[:30]:
            st = f["fixture"]["status"]["short"]
            is_live = st in ["1H","2H","HT","ET","P","LIVE","INT"]
            is_ft = st in ["FT","AET","PEN"]
            home = f["teams"]["home"]["name"]
            away = f["teams"]["away"]["name"]
            league = f"{f['league']['country']} - {f['league']['name']}"
            gh = f["goals"]["home"]
            ga = f["goals"]["away"]
            t = f["fixture"]["date"][11:16]
            if is_ft:
                score = f"{gh}-{ga}"
            elif is_live:
                score = f"{gh}-{ga}"
            else:
                score = "vs"
            games.append({
                "home": home, "away": away, "league": league,
                "score": score, "time": t,
                "live": is_live, "finished": is_ft, "status": st
            })
    except Exception as e:
        print(e)

    if not games:
        games = [
            {"home":"Getafe","away":"Malaga","league":"Spain - LaLiga","score":"1-0","time":"FT","live":False,"finished":True,"status":"FT"},
            {"home":"Atletico Madrid","away":"Real Madrid","league":"Spain - LaLiga","score":"0-0","time":"54'","live":True,"finished":False,"status":"1H"},
            {"home":"Arsenal","away":"Liverpool","league":"England - Premier League","score":"vs","time":"18:30","live":False,"finished":False,"status":"NS"},
        ]
    return games

@app.route("/")
def index():
    live_games = get_today_games_live()
    leagues = [{"id": "eng", "name": "Premier League"}, {"id": "esp", "name": "LaLiga"}, {"id": "ger", "name": "Bundesliga"}]
    return render_template("index.html", live_games=live_games, leagues=leagues, today=datetime.now().strftime("%Y-%m-%d"))

@app.route("/league/<id>")
def league_page(id):
    return "Predictions for " + id

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
