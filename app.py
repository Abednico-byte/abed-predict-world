import os
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

# Token - works from Environment OR hardcoded fallback
SPORTMONKS_TOKEN = os.environ.get("SPORTMONKS_TOKEN", "e4qxeJYaZrPuKEclo0YoYQDLp4cG5hWT63g6SjRubTrCq1XB7KY8fFyJLmPK")

BASE_URL = "https://api.sportmonks.com/v3/football"

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Abed Predict World</title>
<style>
body{font-family:Arial;background:#111;color:#fff;padding:15px}
.card{background:#222;padding:12px;margin:8px 0;border-radius:8px}
.badge{padding:3px 8px;border-radius:4px;font-size:12px}
.live{background:#0f0;color:#000}.upcoming{background:#555}
</style>
</head>
<body>
<h2>SPORTMONKS EVERYTIME - {{ games|length }} games - Day {{ day }}</h2>
<a href="/?day=0">Today</a> | <a href="/?day=1">Tomorrow</a> | <a href="/?day=-1">Yesterday</a>
<hr>
{% if not games %}
<p>NO FIXTURES - Trying to fetch...</p>
<p>Token set: {{ token_ok }}</p>
{% endif %}
{% for g in games %}
<div class="card">
<b>{{ g['name'] }}</b><br>
{{ g['starting_at'] }} - {{ g['state'] }}
<span class="badge {{ 'live' if 'live' in g['state']|lower else 'upcoming' }}">{{ g['state'] }}</span>
</div>
{% endfor %}
</body>
</html>
"""

def get_fixtures(day_offset=0):
    try:
        from datetime import datetime, timedelta
        date = (datetime.now() + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        url = f"{BASE_URL}/fixtures/date/{date}"
        params = {"api_token": SPORTMONKS_TOKEN, "include": "participants"}
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        fixtures = data.get("data", [])
        games = []
        for f in fixtures:
            name = f.get("name", "Match")
            if not f.get("name") and f.get("participants"):
                try:
                    p = f["participants"]
                    name = f"{p[0]['name']} vs {p[1]['name']}"
                except:
                    pass
            games.append({
                "name": name,
                "starting_at": f.get("starting_at", ""),
                "state": f.get("state", {}).get("name", "") if isinstance(f.get("state"), dict) else f.get("state", "")
            })
        return games
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

@app.route("/")
def index():
    day = int(request.args.get("day", 0))
    games = get_fixtures(day)
    token_ok = "YES" if SPORTMONKS_TOKEN else "NO"
    return render_template_string(HTML, games=games, day=day, token_ok=token_ok)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
