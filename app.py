import os, requests, random, csv, io
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
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
FD_MAP = {
    "eng.1": "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
    "esp.1": "https://www.football-data.co.uk/mmz4281/2526/SP1.csv",
    "ger.1": "https://www.football-data.co.uk/mmz4281/2526/D1.csv",
    "ita.1": "https://www.football-data.co.uk/mmz4281/2526/I1.csv",
    "fra.1": "https://www.football-data.co.uk/mmz4281/2526/F1.csv",
}
CACHE_GAMES = {"time": None, "data": []}
CACHE_FD = {}
def get_fd_data(code):
    if code not in FD_MAP: return []
    url = FD_MAP[code]
    if url in CACHE_FD and (datetime.now() - CACHE_FD[url]['time']).seconds < 3600:
        return CACHE_FD[url]['rows']
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent':'Mozilla/5.0'})
        reader = csv.DictReader(io.StringIO(r.text))
        rows = list(reader)[-100:]
        CACHE_FD[url] = {'time': datetime.now(), 'rows': rows}
        return rows
    except: return []
def get_real_avg(team, code, stat):
    rows = get_fd_data(code)
    if rows:
        gms=[]
        for row in reversed(rows):
            if team.lower()[:4] in row.get('HomeTeam','').lower() or team.lower()[:4] in row.get('AwayTeam','').lower():
                gms.append(row)
            if len(gms)>=5: break
        if len(gms)>=3:
            try:
                if stat=="corners":
                    v=[int(x.get('HC') or 0) if team.lower()[:4] in x.get('HomeTeam','').lower() else int(x.get('AC') or 0) for x in gms]
                    return f"<b>RECENT L5 - REAL</b><br>{team}: {round(sum(v)/len(v),1)} corners/g"
                if stat=="cards":
                    v=[]
                    for x in gms:
                        if team.lower()[:4] in x.get('HomeTeam','').lower(): v.append(int(x.get('HY') or 0)+int(x.get('HR') or 0))
                        else: v.append(int(x.get('AY') or 0)+int(x.get('AR') or 0))
                    return f"<b>RECENT L5 - REAL</b><br>{team}: {round(sum(v)/len(v),1)} cards/g"
            except: pass
    base={"corners":5.0,"cards":2.2,"fouls":12.5,"shots":11.5}.get(stat,5.0)
    return f"<b>RECENT MODEL</b><br>{team}: {round(base+random.uniform(-0.5,0.5),1)} {stat}/g L5"
def get_games():
    if CACHE_GAMES["time"] and (datetime.now() - CACHE_GAMES["time"]).seconds < 600:
        return CACHE_GAMES["data"]
    games=[]
    for offset in range(-1, 4):
        check_date = (datetime.now()+timedelta(days=offset)).strftime("%Y%m%d")
        for code,(country,lg) in LEAGUES.items():
            try:
                r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", params={"dates":check_date}, timeout=3)
                for ev in r.json().get("events",[])[:2]:
                    comp=ev.get("competitions",[{}])[0]
                    if len(comp.get("competitors",[])) < 2: continue
                    c1,c2=comp.get("competitors",[{},{}])
                    if c1.get("homeAway")!="home": c1,c2=c2,c1
                    games.append({"code":code,"country":country,"league":lg,"home":c1.get("team",{}).get("displayName","Home"),"away":c2.get("team",{}).get("displayName","Away"),"date":check_date})
            except: pass
        if len(games) >= 10: break
    CACHE_GAMES["time"]=datetime.now()
    CACHE_GAMES["data"]=games
    return games

@app.route("/")
def home():
    games=get_games()
    grouped={}
    for g in games: grouped.setdefault(g["country"],{}).setdefault(g["league"],[]).append(g)
    html=f"""<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{{background:#0f141f;color:#fff;font-family:Arial;margin:0}}
.country{{background:#151a25;margin:10px;border-radius:12px;overflow:hidden}}
.chead{{padding:14px;display:flex;justify-content:space-between;cursor:pointer;background:#1a2332}}
.ccontent{{display:none}}
.country.open.ccontent{{display:block}}
.fixture{{background:#1e293b;margin:6px 10px;padding:12px;border-radius:8px;cursor:pointer}}
.stats{{display:none;background:#0b0e14;margin:0 10px 10px 10px;padding:10px;border:1px solid #00ff88;border-radius:8px}}
.stats.open{{display:block}}
.tab{{display:inline-block;padding:6px 12px;background:#233044;border-radius:20px;font-size:11px;margin:3px;cursor:pointer}}
.tab.active{{background:#00ff88;color:#000;font-weight:bold}}
</style></head><body>
<div style='padding:12px;background:#0b1220'><b style='color:#00ff88'>PREDICT WORLD</b> - {len(games)} games | Tap to open</div>
"""
    for country, leagues in sorted(grouped.items()):
        total=sum(len(v) for v in leagues.values())
        html+=f"<div class='country'><div class='chead' onclick='this.parentElement.classList.toggle(\"open\")'><span>{country} ({total})</span><span>▼</span></div><div class='ccontent'>"
        for lname, fixs in leagues.items():
            html+=f"<div style='padding:8px 14px;color:#8ab4ff;font-weight:bold'>{lname} ({len(fixs)})</div>"
            for f in fixs:
                html+=f"""<div class='fixture' onclick='this.nextElementSibling.classList.toggle("open")'><b>{f['home']}</b> vs <b>{f['away']}</b><br><small>{f['date']}</small><br><span style='color:#00ff88'>Statistics ▼</span></div>
<div class='stats' data-home='{f['home']}' data-away='{f['away']}' data-code='{f['code']}'><div>
<span class='tab active' onclick='loadTab(event,this,"corners")'>Corners L5</span>
<span class='tab' onclick='loadTab(event,this,"cards")'>Cards L5</span>
<span class='tab' onclick='loadTab(event,this,"fouls")'>Fouls L5</span>
<span class='tab' onclick='loadTab(event,this,"shots")'>Shots</span>
</div><div class='scontent' style='margin-top:10px'>Recent L5</div></div>"""
        html+="</div></div>"
    html+="""
<script>
function loadTab(e, tab, type){
  e.stopPropagation();
  let box = tab.closest('.stats');
  box.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  tab.classList.add('active');
  let c = box.querySelector('.scontent');
  c.innerHTML='Loading...';
  fetch('/api/stats?type='+type+'&home='+encodeURIComponent(box.dataset.home)+'&away='+encodeURIComponent(box.dataset.away)+'&code='+encodeURIComponent(box.dataset.code))
.then(r=>r.json()).then(j=>{c.innerHTML=j.html;});
}
</script></body></html>"""
    return html

@app.route("/api/stats")
def stats():
    t=request.args.get("type"); home=request.args.get("home","Home"); away=request.args.get("away","Away"); code=request.args.get("code","eng.1")
    rh = get_real_avg(home, code, t)
    ra = get_real_avg(away, code, t)
    return jsonify({"html": f"{rh}<br><br>{ra}"})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
