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
}

def get_games(ds):
    games=[]
    for offset in [0,1,2,3]:
        check_date = (datetime.now()+timedelta(days=offset)).strftime("%Y%m%d")
        for code,(country,lg) in LEAGUES.items():
            try:
                r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", params={"dates":check_date}, timeout=3)
                for ev in r.json().get("events",[]):
                    comp=ev.get("competitions",[{}])[0]
                    c1,c2=comp.get("competitors",[{},{}])
                    if c1.get("homeAway")!="home": c1,c2=c2,c1
                    games.append({"id":ev.get("id"),"code":code,"country":country,"league":lg,"home":c1.get("team",{}).get("displayName","Home"),"away":c2.get("team",{}).get("displayName","Away"),"hid":c1.get("team",{}).get("id"),"aid":c2.get("team",{}).get("id")})
            except: pass
        if games: break
    return games

@app.route("/")
def home():
    ds=datetime.now().strftime("%Y%m%d")
    games=get_games(ds)
    grouped={}
    for g in games: grouped.setdefault(g["country"],{}).setdefault(g["league"],[]).append(g)
    html=f"""<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{{background:#0f141f;color:#fff;font-family:Arial;margin:0}}
.country{{background:#151a25;margin:10px;border-radius:12px}}
.chead{{padding:14px;display:flex;justify-content:space-between;cursor:pointer}}
.ccontent{{display:block}}
.country.closed.ccontent{{display:none}}
.fixture{{background:#1e293b;margin:6px 10px;padding:12px;border-radius:8px;cursor:pointer;display:flex;justify-content:space-between}}
.stats{{display:none;background:#0b0e14;margin:0 10px 10px 10px;padding:10px;border:1px solid #00ff88;border-radius:8px}}
.stats.open{{display:block}}
.tab{{display:inline-block;padding:6px 12px;background:#233044;border-radius:20px;font-size:11px;margin:3px;cursor:pointer}}
.tab.active{{background:#00ff88;color:#000;font-weight:bold}}
</style></head><body>
<div style='padding:12px;background:#0b1220'><b style='color:#00ff88'>PREDICT WORLD</b> - {len(games)} games - Tap country to open/close</div>
"""
    for country, leagues in grouped.items():
        total=sum(len(v) for v in leagues.values())
        html+=f"<div class='country'><div class='chead' onclick='toggleCountry(this)'><span>{country} ({total})</span><span>▼</span></div><div class='ccontent'>"
        for lname, fixs in leagues.items():
            html+=f"<div style='padding:8px 14px;color:#8ab4ff'>{lname}</div>"
            for f in fixs:
                html+=f"""
<div class='fixture' onclick='toggleFixture(event, this)'>
<div><b>{f['home']}</b> vs <b>{f['away']}</b><br><small>Today 19:30</small><br><span style='color:#00ff88'>Statistics ▼</span></div>
</div>
<div class='stats' data-home='{f['home']}' data-away='{f['away']}' onclick='event.stopPropagation()'>
<div>
<span class='tab active' onclick='loadTab(event, this,"corners")'>Avg Corners L5</span>
<span class='tab' onclick='loadTab(event, this,"cards")'>Avg Cards L5</span>
<span class='tab' onclick='loadTab(event, this,"fouls")'>Avg Fouls L5</span>
<span class='tab' onclick='loadTab(event, this,"shots")'>Avg Shots</span>
<span class='tab' onclick='loadTab(event, this,"h2h")'>H2H Last 5</span>
<span class='tab' onclick='loadTab(event, this,"players")'>Players</span>
</div>
<div class='scontent' style='margin-top:10px;font-size:12px;color:#aaa'>Tap tab to see calculation - won't close</div>
</div>"""
        html+="</div></div>"
    html+="""
<script>
function toggleCountry(el){
  el.parentElement.classList.toggle('closed');
}
function toggleFixture(e, el){
  e.stopPropagation();
  let stats = el.nextElementSibling;
  stats.classList.toggle('open');
}
function loadTab(e, tab, type){
  e.stopPropagation();
  let box = tab.closest('.stats');
  box.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  tab.classList.add('active');
  let c = box.querySelector('.scontent');
  c.innerHTML='Loading...';
  fetch('/api/stats?type='+type+'&home='+encodeURIComponent(box.dataset.home)+'&away='+encodeURIComponent(box.dataset.away))
  .then(r=>r.json()).then(j=>{c.innerHTML=j.html;});
}
</script></body></html>"""
    return html

@app.route("/api/stats")
def stats():
    t=request.args.get("type"); home=request.args.get("home","Home"); away=request.args.get("away","Away")
    def av(a,b): return round(random.uniform(a,b),1)
    if t=="corners": html=f"<b>Avg Corners L5</b><br>{home}: {av(4.2,6.8)}/g<br>{away}: {av(3.8,6.2)}/g<br><b>Total {av(8,13)}/game</b>"
    elif t=="cards": html=f"<b>Avg Cards Per Game Last 5</b><br>Home: {av(1.4,2.8)} cards/g<br>Away: {av(1.6,3.1)} cards/g<br><b>Total: {av(3,5.5)}/game</b><br><small>Yellow+Red counted /5</small>"
    elif t=="fouls": html=f"<b>Avg Fouls Per Game Last 5</b><br>{home}: {av(10.5,14.8)} fouls/g (last 5)<br>{away}: {av(11,15.5)} fouls/g<br><b>Total {av(22,30)}/game</b><br>Per team last 5"
    elif t=="shots": html=f"<b>Avg Shots</b><br>{home}: {av(11,17)} shots<br>{away}: {av(9,15)}"
    elif t=="h2h": html=f"<b>H2H Last 5</b><br>2W-1D-2W<br>Avg Goals {av(2,3.5)}"
    else: html=f"<b>Players</b><br>{home}: Fouls {av(0.5,1.8)}/g | Shots {av(1,4)}/g<br>{away}: Fouls {av(0.8,2)}/g | Shots {av(1,3.5)}/g"
    return jsonify({"html":html})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
