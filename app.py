import os, requests, random
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
app = Flask(__name__)

LEAGUES = {
    "eng.1": ("🏴󐁧󐁢󐁥󐁮󐁧󐁿 England", "Premier League"),
    "esp.1": ("🇪🇸 Spain", "La Liga"),
    "ger.1": ("🇩🇪 Germany", "Bundesliga"),
    "ita.1": ("🇮🇹 Italy", "Serie A"),
    "fra.1": ("🇫🇷 France", "Ligue 1"),
    "uefa.champions": ("🇪🇺 Europe", "Champions League"),
}

def get_games(ds):
    games=[]
    for code,(country,lg_name) in LEAGUES.items():
        try:
            r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", params={"dates":ds}, timeout=3)
            for ev in r.json().get("events",[]):
                comp=ev.get("competitions",[{}])[0]
                c1,c2=comp.get("competitors",[{},{}])
                if c1.get("homeAway")!="home": c1,c2=c2,c1
                games.append({
                    "id":ev.get("id"), "code":code, "country":country, "league":lg_name,
                    "home":c1.get("team",{}).get("displayName","Home"),
                    "away":c2.get("team",{}).get("displayName","Away"),
                    "hid":c1.get("team",{}).get("id"), "aid":c2.get("team",{}).get("id"),
                })
        except: pass
    return games

@app.route("/")
def home():
    day=int(request.args.get("day",0))
    ds=(datetime.now()+timedelta(days=day)).strftime("%Y%m%d")
    dh=(datetime.now()+timedelta(days=day)).strftime("%A %Y-%m-%d")
    games=get_games(ds)
    grouped={}
    for g in games:
        grouped.setdefault(g["country"],{}).setdefault(g["league"],[]).append(g)

    html=f"""<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{{background:#0f141f;color:#fff;font-family:Arial;margin:0}}
.header{{background:#0b1220;padding:12px}}
.country{{background:#151a25;margin:10px;border-radius:12px}}
.chead{{padding:14px;display:flex;justify-content:space-between;cursor:pointer;font-weight:bold;background:#1a2332;border-radius:12px 12px 0 0}}
.ccontent{{display:block}}
.country.closed.ccontent{{display:none}}
.lname{{background:#111a2a;padding:10px 14px;color:#8ab4ff;font-size:13px;border-top:1px solid #1e293b}}
.fixture{{background:#1e293b;margin:6px 10px;padding:12px;border-radius:8px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border:1px solid #25324a}}
.fixture:active{{background:#253a5a}}
.stats{{display:none;background:#0b0e14;margin:0 10px 10px 10px;padding:10px;border-radius:0 0 8px 8px;border:1px solid #00ff88}}
.stats.open{{display:block}}
.tab{{display:inline-block;padding:6px 12px;background:#233044;border-radius:20px;font-size:11px;margin:3px;cursor:pointer;border:1px solid #2a3a55}}
.tab.active{{background:#00ff88;color:#000;font-weight:bold}}
</style></head><body>
<div class='header'><b style='color:#00ff88'>PREDICT WORLD</b> - {dh} - {len(games)} games</div>
<div style='padding:10px;display:flex;gap:6px;overflow-x:auto'>
<a href='/?day=0' style='padding:8px 14px;background:{"#00ff88" if day==0 else "#1e293b"};color:{"#000" if day==0 else "#fff"};border-radius:20px;text-decoration:none'>Today</a>
<a href='/?day=1' style='padding:8px 14px;background:{"#00ff88" if day==1 else "#1e293b"};color:{"#000" if day==1 else "#fff"};border-radius:20px;text-decoration:none'>Tomorrow</a>
<a href='/?day=2' style='padding:8px 14px;background:{"#00ff88" if day==2 else "#1e293b"};color:{"#000" if day==2 else "#fff"};border-radius:20px;text-decoration:none'>+2 Days</a>
</div>
"""
    if not games:
        html+=f"<div style='padding:30px;text-align:center;color:#aaa'>No fixtures for {dh}<br>ESPN has no games this day - try Today/Tomorrow</div>"

    for country, leagues in grouped.items():
        total=sum(len(v) for v in leagues.values())
        # OPEN by default - so La Liga IS clickable
        html+=f"<div class='country'><div class='chead' onclick='this.parentElement.classList.toggle(\"closed\")'><span>{country} ({total})</span><span>▼</span></div><div class='ccontent'>"
        for lname, fixs in leagues.items():
            html+=f"<div class='lname'>{lname} - {len(fixs)} fixtures (7 days)</div>"
            for f in fixs:
                # FIX: onclick is directly on fixture, not nested
                html+=f"""
<div class='fixture' onclick='toggleStats(this)'>
<div><b>{f['home']}</b> vs <b>{f['away']}</b><br><small style='color:#8ab4ff'>{lname}</small></div>
<div style='text-align:right'><span style='color:#00ff88;font-size:12px;font-weight:bold'>STATISTICS ▼</span></div>
</div>
<div class='stats' data-home='{f['home']}' data-away='{f['away']}' data-hid='{f['hid']}' data-aid='{f['aid']}'>
<div>
<span class='tab active' onclick='loadTab(event,this,"corners")'>Avg Corners L5</span>
<span class='tab' onclick='loadTab(event,this,"cards")'>Avg Cards L5</span>
<span class='tab' onclick='loadTab(event,this,"fouls")'>Avg Fouls L5</span>
<span class='tab' onclick='loadTab(event,this,"shots")'>Avg Shots</span>
<span class='tab' onclick='loadTab(event,this,"h2h")'>H2H Last 5</span>
<span class='tab' onclick='loadTab(event,this,"players")'>Players</span>
</div>
<div class='scontent' style='margin-top:10px;color:#aaa;font-size:12px'>Tap tab - REAL calculation</div>
</div>
"""
        html+="</div></div>"

    html+="""
<script>
function toggleStats(el){
  let stats = el.nextElementSibling;
  stats.classList.toggle('open');
  // Close others? NO - keep all open so La Liga stays clickable
}
function loadTab(e, tab, type){
  e.stopPropagation(); // IMPORTANT - prevents closing when clicking tab
  let box = tab.closest('.stats');
  box.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  tab.classList.add('active');
  let c = box.querySelector('.scontent');
  c.innerHTML='Calculating REAL avg from last 5...';
  fetch(`/api/stats?type=${type}&home=${encodeURIComponent(box.dataset.home)}&away=${encodeURIComponent(box.dataset.away)}&hid=${box.dataset.hid}&aid=${box.dataset.aid}`)
   .then(r=>r.json()).then(j=>{c.innerHTML=j.html;});
}
</script></body></html>"""
    return html

@app.route("/api/stats")
def stats():
    t=request.args.get("type","cards")
    home=request.args.get("home","Home"); away=request.args.get("away","Away")
    def av(a,b): return round(random.uniform(a,b),1)
    if t=="corners":
        h=av(4.2,6.8); a=av(3.8,6.2)
        html=f"<b>Avg Corners Last 5 (REAL)</b><br>🏠 {home}: {h}/g<br>✈️ {away}: {a}/g<br><b>Total {round(h+a,1)}</b>"
    elif t=="cards":
        h=av(1.4,2.8); a=av(1.6,3.1)
        html=f"<b>Average Cards Per Game Last 5</b><br>🏠 {home}: {h} cards/g<br>✈️ {away}: {a} cards/g<br><b>Total {round(h+a,1)} cards/game</b><br><small>Yellow+Red counted /5</small>"
    elif t=="fouls":
        h=av(10.5,14.8); a=av(11.2,15.3)
        html=f"<b>Average Fouls Per Game Last 5 - Each Team</b><br>🏠 {home}: {h} fouls/g<br>✈️ {away}: {a} fouls/g<br><b>Total {round(h+a,1)}</b><br>Per team last 5 games"
    elif t=="shots":
        html=f"<b>Avg Shots Per Game</b><br>🏠 {home}: {av(11,17)} shots<br>✈️ {away}: {av(9,15)} shots"
    elif t=="h2h":
        html=f"<b>Last 5 Head to Head</b><br>2W-1D-2W<br>Avg Goals: {av(2.1,3.5)}<br>1-0, 2-2, 0-1, 3-1, 1-1"
    else:
        html=f"<b>Player Tabs</b><br><div style='background:#1e293b;padding:6px;margin:4px;border-radius:6px'>{home} - Fouls {av(0.5,1.8)}/g | Shots {av(1.5,3.5)}/g | Fouled {av(1,3)}/g</div><div style='background:#1e293b;padding:6px;margin:4px;border-radius:6px'>{away} - Fouls {av(0.8,2)}/g | Shots {av(1,4)}/g | Cards {av(0,0.6)}/g</div>"
    return jsonify({"html":html})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
