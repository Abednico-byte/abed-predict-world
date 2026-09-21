import os, requests
from datetime import datetime, timedelta
from flask import Flask, request
app = Flask(__name__)
TOKEN = os.environ.get("SPORTMONKS_TOKEN", "e4qxeJYaZrPuKEclo0YoYQDLp4cG5hWT63g6SjRubTrCq1XB7KY8fFyJLmPK")

# ESPN - FREE, NO KEY, NEVER BLOCKS, ALL LEAGUES
ESPN_LEAGUES = [
    "eng.1", # Premier League
    "esp.1", # La Liga
    "ger.1", # Bundesliga
    "ita.1", # Serie A
    "fra.1", # Ligue 1
    "uefa.champions", # Champions League
    "uefa.europa", # Europa League
    "uefa.europa.conf",# Conference
    "eng.2", # Championship
    "ned.1", # Eredivisie
    "por.1", # Portugal
]

def fetch_espn(date_str):
    games = []
    for league in ESPN_LEAGUES:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
            r = requests.get(url, params={"dates": date_str.replace("-","")}, timeout=8)
            j = r.json()
            for ev in j.get("events", []):
                comp = ev.get("competitions", [{}])[0]
                home = comp.get("competitors", [{},{}])[0]
                away = comp.get("competitors", [{},{}])[1]
                # fix home/away order
                if home.get("homeAway")!= "home":
                    home, away = away, home
                h_name = home.get("team",{}).get("displayName","Home")
                a_name = away.get("team",{}).get("displayName","Away")
                h_score = home.get("score","")
                a_score = away.get("score","")
                status = comp.get("status",{}).get("type",{}).get("description","")
                games.append({
                    "name": f"{h_name} vs {a_name}",
                    "score": f"{h_score}-{a_score}" if h_score!="" else "",
                    "status": status,
                    "league": league
                })
        except:
            continue
    return games

def fetch_sportmonks(s, e):
    try:
        url = f"https://api.sportmonks.com/v3/football/fixtures/between/{s}/{e}"
        r = requests.get(url, params={"api_token": TOKEN, "include": "participants", "per_page": 50}, timeout=10)
        data = r.json().get("data", [])
        out=[]
        for g in data:
            try:
                p=g.get("participants",[])
                hn = next((x["name"] for x in p if x.get("meta",{}).get("location")=="home"), p[0]["name"])
                an = next((x["name"] for x in p if x.get("meta",{}).get("location")=="away"), p[1]["name"])
                out.append({"name": f"{hn} vs {an}", "score":"", "status":"", "league":"sportmonks"})
            except:
                pass
        return out
    except:
        return []

@app.route("/")
def home():
    day = int(request.args.get("day", 0))
    base = datetime.now() + timedelta(days=day)
    s = base.strftime("%Y-%m-%d")

    espn_games = fetch_espn(s)
    sm_games = fetch_sportmonks(s, (base+timedelta(days=1)).strftime("%Y-%m-%d"))

    all_games = espn_games + sm_games

    html = f"<body style='background:#111;color:#fff;font-family:Arial;padding:15px'>"
    html += f"<h2>FOOTBALL - {len(all_games)} games - {s}</h2>"
    html += "<a href='/?day=-1' style='color:#0ff'>Yesterday Results</a> | "
    html += "<a href='/?day=0' style='color:#0ff'>Today</a> | "
    html += "<a href='/?day=1' style='color:#0ff'>Tomorrow</a><hr>"
    html += f"<p>ESPN free: {len(espn_games)} | SportMonks: {len(sm_games)}</p>"

    if not all_games:
        html += "<p>No fixtures found for this date</p>"
    else:
        for g in all_games[:150]:
            html += f"<div style='background:#222;padding:10px;margin:6px;border-radius:8px'>{g['name']} <b style='color:#0f0'>{g['score']}</b><br><small>{g['status']} | {g['league']}</small></div>"

    return html + "</body>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
