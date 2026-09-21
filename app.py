import os, requests
from datetime import datetime, timedelta
from flask import Flask, request

app = Flask(__name__)
TOKEN = os.environ.get("SPORTMONKS_TOKEN", "e4qxeJYaZrPuKEclo0YoYQDLp4cG5hWT63g6SjRubTrCq1XB7KY8fFyJLmPK")

@app.route("/")
def home():
    day = int(request.args.get("day", 0))
    target = datetime.now() + timedelta(days=day)
    start = target.strftime("%Y-%m-%d")
    end = (target + timedelta(days=1)).strftime("%Y-%m-%d")

    games = []
    error_msg = ""
    try:
        # Use BETWEEN - works on free plan
        url = f"https://api.sportmonks.com/v3/football/fixtures/between/{start}/{end}"
        params = {
            "api_token": TOKEN,
            "include": "participants;state;league",
            "per_page": "100"
        }
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        if "data" in data:
            games = data["data"]
        else:
            error_msg = str(data)[:300]
    except Exception as e:
        error_msg = str(e)

    html = f"""
    <body style='background:#111;color:#fff;font-family:Arial;padding:15px'>
    <h2>SPORTMONKS EVERYTIME - {len(games)} games - Day {day}</h2>
    <a href='/?day=-1'>Yesterday</a> | <a href='/?day=0'>Today</a> | <a href='/?day=1'>Tomorrow</a>
    <hr>
    """
    if error_msg:
        html += f"<p style='color:orange'>API response: {error_msg}</p>"

    if not games:
        html += "<p>NO FIXTURES - Trying to fetch...</p><p>Token set: YES</p>"
        html += f"<p>Checked: {start} to {end}</p>"
        # Try livescores as backup
        try:
            r2 = requests.get("https://api.sportmonks.com/v3/football/livescores/inplay", params={"api_token": TOKEN, "include": "participants"}, timeout=10)
            live = r2.json().get("data", [])
            html += f"<p>Live in-play found: {len(live)} games</p>"
            games = live
        except:
            pass
    else:
        for g in games[:100]:
            name = g.get("name", "Match")
            try:
                if g.get("participants"):
                    p = g["participants"]
                    # find home/away
                    home = next((x["name"] for x in p if x.get("meta",{}).get("location")=="home"), p[0]["name"])
                    away = next((x["name"] for x in p if x.get("meta",{}).get("location")=="away"), p[1]["name"] if len(p)>1 else "")
                    name = f"{home} vs {away}"
            except:
                pass
            state = g.get("state", {}).get("name", "") if isinstance(g.get("state"), dict) else str(g.get("state",""))
            html += f"<div style='background:#222;padding:10px;margin:6px;border-radius:8px'>{name}<br><small>{g.get('starting_at','')} - {state}</small></div>"

    return html + "</body>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
