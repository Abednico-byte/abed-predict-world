import os, requests, random, csv, io
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

LEAGUES = {
    "eng.1": ("🏴󐁧󐁢󐁥󐁮󐁧󐁿 England", "Premier League"),
    "esp.1": ("🇪🇸 Spain", "La Liga"),
    "ger.1": ("🇩🇪 Germany", "Bundesliga"),
    "ita.1": ("🇮🇹 Italy", "Serie A"),
    "fra.1": ("🇫🇷 France", "Ligue 1"),
    "ned.1": ("🇳🇱 Netherlands", "Eredivisie"),
    "por.1": ("🇵🇹 Portugal", "Primeira Liga"),
    "bel.1": ("🇧🇪 Belgium", "Jupiler Pro"),
    "tur.1": ("🇹🇷 Turkey", "Super Lig"),
    "nor.1": ("🇳🇴 Norway", "Eliteserien"),
    "swe.1": ("🇸🇪 Sweden", "Allsvenskan"),
    "den.1": ("🇩🇰 Denmark", "Superliga"),
    "cro.1": ("🇭🇷 Croatia", "HNL"),
    "usa.1": ("🇺🇸 USA", "MLS"),
    "uefa.champions": ("🇪🇺 UEFA", "Champions League"),
}

CACHE_GAMES = {"time": None, "data": [], "loading": False}
CACHE_FD = {}

def fetch_one(args):
    check_date, display_date, code, country, lg = args
    try:
        r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard",
                         params={"dates": check_date}, timeout=4)
        events = r.json().get("events", [])
        out = []
        for ev in events:
            comp = ev.get("competitions", [{}])[0]
            if len(comp.get("competitors", [])) < 2: continue
            c1, c2 = comp.get("competitors", [{}, {}])
            if c1.get("homeAway")!= "home": c1, c2 = c2, c1
            out.append({
                "code": code, "country": country, "league": lg,
                "home": c1.get("team", {}).get("displayName", "Home"),
                "away": c2.get("team", {}).get("displayName", "Away"),
                "date": display_date, "time": comp.get("date","")[11:16] if comp.get("date") else ""
            })
        return out
    except:
        return []

def get_games():
    # Return cache if fresh (15 min)
    if CACHE_GAMES["time"] and (datetime.now() - CACHE_GAMES["time"]).seconds < 900:
        return CACHE_GAMES["data"]

    # If already loading, return old cache to avoid double load
    if CACHE_GAMES["loading"]:
        return CACHE_GAMES["data"]

    CACHE_GAMES["loading"] = True
    tasks = []
    for offset in range(0, 7):
        check_date = (datetime.now()+timedelta(days=offset)).strftime("%Y%m%d")
        display_date = (datetime.now()+timedelta(days=offset)).strftime("%a %d %b")
        for code, (country, lg) in LEAGUES.items():
            tasks.append((check_date, display_date, code, country, lg))

    games = []
    # PARALLEL - 20 at a time = 10x faster
    with ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(fetch_one, t) for t in tasks]
        for f in as_completed(futures):
            games.extend(f.result())

    CACHE_GAMES["time"] = datetime.now()
    CACHE_GAMES["data"] = games
    CACHE_GAMES["loading"] = False
    return games

@app.route("/")
def home():
    games = get_games()
    grouped = {}
    for g in games: grouped.setdefault(g["country"], {}).setdefault(g["league"], []).append(g)

    html = f"""<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{{background:#0f141f;color:#fff;font-family:Arial;margin:0}}
.country{{background:#151a25;margin:8px;border-radius:12px;overflow:hidden}}
.chead{{padding:14px;display:flex;justify-content:space-between;cursor:pointer;background:#1a2332}}
.ccontent{{display:none}}
.country.open.ccontent{{display:block}}
.league-head{{padding:10px 14px;color:#8ab4ff;background:#0f1a2a;margin-top:2px;font-size:13px;font-weight:bold;display:flex;justify-content:space-between}}
.fixture{{background:#1e293b;margin:4px 8px;padding:10px;border-radius:8px;cursor:pointer}}
.stats{{display:none;background:#0b0e14;margin:0 8px 8px 8px;padding:10px;border:1px solid #00ff88;border-radius:8px}}
.stats.open{{display:block}}
.tab{{display:inline-block;padding:5px 10px;background:#233044;border-radius:20px;font-size:11px;margin:2px;cursor:pointer}}
.tab.active{{background:#00ff88;color:#000;font-weight:bold}}
</style></head><body>
<div style='padding:12px;background:#0b1220'><b style='color:#00ff88'>PREDICT WORLD</b> - {len(games)} games (7 days) | FAST</div>
"""
    for country, leagues in sorted(grouped.items()):
        total = sum(len(v) for v in leagues.values())
        html += f"<div class='country'><div class='chead' onclick='this.parentElement.classList.toggle(\"open\")'><span>{country} ({total})</span><span>▼</span></div><div class='ccontent'>"
        for lname, fixs in leagues.items():
            html += f"<div class='league-head'><span>{lname}</span><span>{len(fixs)}</span></div>"
            for f in fixs[:10]: # show max 10 per league to keep fast
                html += f"""<div class='fixture' onclick='this.nextElementSibling.classList.toggle("open")'>
<b>{f['home']}</b> vs <b>{f['away']}</b><br>
<small>{f['date']} {f['time']}</small><br><span style='color:#00ff88'>Stats ▼</span></div>
<div class='stats' data-home='{f['home']}' data-away='{f['away']}' data-code='{f['code']}'><div>
<span class='tab active' onclick='loadTab(event,this,"corners")'>Corners L5</span>
<span class='tab' onclick='loadTab(event,this,"cards")'>Cards L5</span>
<span class='tab' onclick='loadTab(event,this,"fouls")'>Fouls L5</span>
<span class='tab' onclick='loadTab(event,this,"shots")'>Shots</span>
</div><div class='scontent' style='margin-top:10px'>Recent L5</div></div>"""
        html += "</div></div>"

    html += """
<script>
function loadTab(e, tab, type){
  e.stopPropagation();
  let box = tab.closest('.stats');
  box.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  tab.classList.add('active');
  let c = box.querySelector('.scontent');
  c.innerHTML='Loading...';
  fetch('/api/stats?type='+type+'&home='+encodeURIComponent(box.dataset.home)+'&away='+encodeURIComponent(box.dataset.away)+'&code='+box.dataset.code)
.then(r=>r.json()).then(j=>{c.innerHTML=j.html;});
}
</script></body></html>"""
    return html

@app.route("/api/stats")
def stats_api():
    t = request.args.get("type","corners")
    home = request.args.get("home","Home")
    code = request.args.get("code","eng.1")
    # Fast recent mock - no CSV load to keep instant
    base = {"corners":5.1,"cards":2.3,"fouls":12.8
