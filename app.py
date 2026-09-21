import os, requests
from datetime import datetime, timedelta
from flask import Flask, request
app = Flask(__name__)

TOKEN = os.environ.get("SPORTMONKS_TOKEN", "e4qxeJYaZrPuKEclo0YoYQDLp4cG5hWT63g6SjRubTrCq1XB7KY8fFyJLmPK")

def fetch_range(start_date, end_date):
    try:
        url = f"https://api.sportmonks.com/v3/football/fixtures/between/{start_date}/{end_date}"
        r = requests.get(url, params={
            "api_token": TOKEN,
            "include": "participants;state;scores;league",
            "per_page": 100
        }, timeout=20)
        j = r.json()
        return j.get("data", [])
    except Exception as e:
        print(e)
        return []

@app.route("/")
def index():
    day = int(request.args.get("day", 0))
    base = datetime.now() + timedelta(days=day)

    # For day= -1 show yesterday results, day 0 today, day 1 tomorrow
    if day == -1:
        s = (base - timedelta(days=1)).strftime("%Y-%m-%d")
        e = base.strftime("%Y-%m-%d")
    else:
        s = base.strftime("%Y-%m-%d")
        e = (base + timedelta(days=1)).strftime("%Y-%m-%d")

    games = fetch_range(s, e)

    html = f"<body style='background:#0f1115;color:#fff;font-family:Arial;padding:15px'>"
    html += f"<h2>SPORTMONKS EVERYTIME - {len(games)} games</h2>"
    html += f"<a href='/?day=-1' style='color:#0ff'>Yesterday Results</a> | "
    html += f"<a href='/?day=0' style='color:#0ff'>Today</a> | "
    html += f"<a href='/?day=1' style='color:#0ff'>Tomorrow</a><hr>"

    if not games:
        html += f"<p>NO FIXTURES FOR {s} to {e}</p>"
        html += f"<p>Token: YES - Plan is FREE so some days are empty. Try Yesterday.</p>"
        # backup: try last 7 days to prove API works
        g7 = fetch_range((datetime.now()-timedelta(days=3)).strftime("%Y-%m-%d"), (datetime.now()+timedelta(days=3)).strftime("%Y-%m-%d"))
        html += f"<p>Last 7 days total games found: {len(g7)}</p>"
    else:
        for g in games:
            try:
                parts = g.get("participants", [])
                home = next((p["name"] for p in parts if p.get("meta",{}).get("location")=="home"), "Home")
                away = next((p["name"] for p in parts if p.get("meta",{}).get("location")=="away"), "Away")
                name = f"{home} vs {away}"
            except:
                name = g.get("name","Match")

            # score for yesterday
            score_txt = ""
            if g.get("scores"):
                try:
                    cur = [s for s in g["scores"] if s.get("description")=="CURRENT"]
                    if cur:
                        hg = next((c["score"]["goals"] for c in cur if c["score"]["participant"]=="home"), 0)
                        ag = next((c["score"]["goals"] for c in cur if c["score"]["participant"]=="away"), 0)
                        score_txt = f" {hg}-{ag}"
                except:
                    pass

            state = g.get("state",{}).get("name","") if isinstance(g.get("state"),dict) else ""
            html += f"<div style='background:#222;padding:10px;margin:6px;border-radius:8px'>{name}<b style='color:#0f0'>{score_txt}</b><br><small>{g.get('starting_at','')} | {state} | {g.get('league',{}).get('name','') if isinstance(g.get('league'),dict) else ''}</small></div>"

    return html + "</body>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
