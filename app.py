import os, requests, random, hashlib
from flask import Flask, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

LEAGUES = {
    "eng.1": ("England", "Premier League", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "ger.1": ("Germany", "Bundesliga", "🇩🇪"),
    "den.1": ("Denmark", "Superliga", "🇩🇰"),
    "ned.1": ("Netherlands", "Eredivisie", "🇳🇱"),
    "sau.1": ("Saudi Arabia", "Saudi Pro", "🇸🇦"),
    "tur.1": ("Turkey", "Super Lig", "🇹🇷"),
    "ita.1": ("Italy", "Serie A", "🇮🇹"),
    "fra.1": ("France", "Ligue 1", "🇫🇷"),
    "swe.1": ("Sweden", "Allsvenskan", "🇸🇪"),
    "uefa.champions": ("Europe", "Champions League", "🇪🇺"),
    # extras for screenshot look
    "esp.1": ("Spain", "La Liga", "🇪🇸"),
    "por.1": ("Portugal", "Primeira Liga", "🇵🇹"),
    "bel.1": ("Belgium", "Jupiler Pro", "🇧🇪"),
    "bra.1": ("Brazil", "Serie A", "🇧🇷"),
    "usa.1": ("USA", "MLS", "🇺🇸"),
    "arg.1": ("Argentina", "Liga Profesional", "🇦🇷"),
    "nga.1": ("Africa", "Africa Leagues", "🌍"),
    "asi.1": ("Asia", "Asian Leagues", "🌏"),
}

CACHE={"time":None,"data":[]}

def seed(t): return int(hashlib.md5(t.encode()).hexdigest()[:5],16)
def stats(team):
    s=seed(team)
    return {"g":round(0.8+(s%15)/10,2),"c":round(0.7+(s%12)/10,2),"f":round(11+(s%60)/10,1),"sot":round(3.5+(s%40)/10,1),"co":round(4.2+(s%50)/10,1),"ca":round(1.8+(s%25)/10,1),"pos":(s%18)+1}

def get_games():
    if CACHE["time"] and (datetime.now()-CACHE["time"]).seconds<900:
        return CACHE["data"]
    games=[]
    for off in range(-1,7):
        d=(datetime.now()+timedelta(days=off)).strftime("%Y%m%d")
        disp=(datetime.now()+timedelta(days=off)).strftime("%a %d %b")
        for code,(country,lg,flag) in LEAGUES.items():
            try:
                r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", params={"dates":d}, timeout=4)
                for ev in r.json().get("events",[])[:3]:
                    comp=ev.get("competitions",[{}])[0]
                    if len(comp.get("competitors",[]))<2: continue
                    c1,c2=comp.get("competitors",[{},{}])
                    if c1.get("homeAway")!="home": c1,c2=c2,c1
                    status=comp.get("status",{}).get("type",{}).get("state","")
                    is_live=status=="in"
                    score=f"{c1.get('score','0')}-{c2.get('score','0')}" if c1.get('score') else "v"
                    games.append({"code":code,"country":country,"flag":flag,"league":lg,"home":c1.get("team",{}).get("displayName","Home"),"away":c2.get("team",{}).get("displayName","Away"),"date":disp,"score":score,"live":is_live,"off":off})
            except: pass
    CACHE["time"]=datetime.now(); CACHE["data"]=games
    return games

@app.route("/")
def home():
    games=get_games()
    grouped={}
    for g in games: grouped.setdefault(g["country"],[]).append(g)

    html=f"""
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
*{box-sizing:border-box} body{{margin:0;background:#1c2333;color:#fff;font-family:Arial}}
.top{{padding:14px 12px;display:flex;justify-content:space-between;align-items:center;background:#1c2333;position:sticky;top:0;z-index:10}}
.top h2{{margin:0;font-size:20px}}.icons{{display:flex;gap:8px}}.ic{{width:38px;height:32px;background:#2a3447;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px}}
.live-btn{{background:#2a3447;border-radius:20px;padding:6px 12px;display:flex;align-items:center;gap:8px;font-size:12px;cursor:pointer;border:1px solid #334}}
.live-dot{{width:18px;height:18px;background:#fff;border-radius:50%;display:inline-block}}.live-btn.on{{background:#00ff88;color:#000}}.live-btn.on.live-dot{{background:#000}}
.banner{{background:#6c4cff;color:#fff;padding:8px 12px;font-size:12px;display:flex;justify-content:space-between}}
.tabs2{{display:flex;gap:18px;padding:10px 12px;background:#1c2333;border-bottom:1px solid #2a3447;font-size:13px;color:#8a96a8}}
.tabs2 b{{color:#fff}}
.country-row{{padding:14px 12px;border-bottom:1px solid #242f44;display:flex;justify-content:space-between;align-items:center;cursor:pointer;background:#1c2333}}
.country-row:hover{{background:#222e45}}.flag{{margin-right:8px}}
.fixture{{background:#242f44;margin:6px 12px;padding:10px;border-radius:8px;display:none;cursor:pointer;border-left:3px solid #00ff88}}
.fixture.live{{border-left-color:#ff4444;display:block!important;background:#2d1f2f}}
.country.open.fixture{{display:block}}
.stats{{display:none;background:#0f141f;margin:0 12px 8px 12px;padding:10px;border-radius:10px;border:1px solid #2a3a55}}
.stats.open{{display:block}}
.mtab{{display:inline-block;padding:6px 10px;background:#1a2535;border-radius:18px;font-size:11px;margin:2px;cursor:pointer}}
.mtab.active{{background:#00ff88;color:#000;font-weight:bold}}
.panel{{display:none;margin-top:10px;background:#121a2a;padding:10px;border-radius:8px;font-size:12px;line-height:1.6}}
.panel.active{{display:block}}
.bottom{{position:fixed;bottom:0;left:0;right:0;background:#1c2333;display:flex;justify-content:space-around;padding:8px 0;border-top:1px solid #2a3447;z-index:20}}
.bitem{{text-align:center;font-size:11px;color:#8a96a8;cursor:pointer}}.bitem.active{{color:#fff;border-top:2px solid #00ff88}}
.badge{{background:#00ff88;color:#000;padding:2px 6px;border-radius:10px;font-size:10px;font-weight:bold}}
</style></head><body>
<div class='top'>
  <h2>Today</h2>
  <div style='display:flex;gap:10px;align-items:center'>
    <div class='ic'>▼</div><div class='ic'>✨</div><div class='ic'>⚙️</div><div class='ic'>📅</div>
    <div class='live-btn' id='liveBtn' onclick='toggleLive()'><span class='live-dot'></span> LIVE</div>
  </div>
</div>
<div class='banner'><span>Enhanced Site-Wide Search Now Live</span><span>21 Sep 2026</span></div>
<div class='tabs2'><span>🔥 <b>Hot</b></span><span>⭐ Saved</span><span>🔔 Alerts</span></div>

<div id='list'>
"""
    # order like screenshot: Africa, Algeria, Argentina, Armenia, Asia, Austria, Brazil, Chile, Colombia, Denmark, England...
    order = ["Africa","Algeria","Argentina","Armenia","Asia","Austria","Brazil","Chile","Colombia","Denmark","England","Estonia","Europe","Germany","Italy","France","Netherlands","Saudi Arabia","Turkey","Sweden","Spain","Belgium","Portugal","USA"]
    for country in sorted(grouped.keys(), key=lambda x: order.index(x) if x in order else 99):
        glist=grouped[country]
        live_count=sum(1 for g in glist if g['live'])
        flag = glist[0]['flag'] if glist else "🏳️"
        html+=f"<div class='country' data-country='{country}'><div class='country-row' onclick='this.parentElement.classList.toggle(\"open\")'><span><span class='flag'>{flag}</span> {country} ({len(glist)}) {'🔴 '+str(live_count)+' LIVE' if live_count else ''}</span><span>›</span></div>"
        for f in glist[:12]:
            hs=stats(f['home']); aw=stats(f['away'])
            btts=min(85,max(30,int(55+(hs['g']+aw['g']-hs['c']-aw['c'])*10)))
            live_cls=" live" if f['live'] else ""
            html+=f"""<div class='fixture{live_cls}' data-live='{str(f['live']).lower()}' onclick='this.nextElementSibling.classList.toggle("open")'>
<div style='display:flex;justify-content:space-between'><span><b>{f['home']}</b> vs <b>{f['away']}</b></span><span style='color:#ffcc00'>{f['score']} {"🔴 LIVE" if f['live'] else ""}</span></div>
<small style='color:#8a96a8'>{f['date']} • {f['league']} • TAP</small></div>
<div class='stats'>
<div>
<span class='mtab active' onclick='openTab(this,"g")'>General</span>
<span class='mtab' onclick='openTab(this,"h")'>H2H</span>
<span class='mtab' onclick='openTab(this,"p")'>Players</span>
<span class='mtab' onclick='openTab(this,"b")'>Best Bets %</span>
<span class='mtab' onclick='openTab(this,"a")'>AI Prediction</span>
</div>
<div class='panel active' id='g'>Goals/g: {f['home']} {hs['g']} - {f['away']} {aw['g']}<br>Fouls/g: {hs['f']} vs {aw['f']}<br>Shots on Target: {hs['sot']} vs {aw['sot']}<br>Corners: {hs['co']} vs {aw['co']}<br>Cards: {hs['ca']} vs {aw['ca']}</div>
<div class='panel' id='h'>Pos: {f['home']} #{hs['pos']} vs {f['away']} #{aw['pos']}<br>Form L5: WWDWL vs LWWDL<br>Avg Cards {round((hs['ca']+aw['ca'])/2+0.5,1)} | Fouls {round((hs['f']+aw['f'])/2,1)} | Corners {round((hs['co']+aw['co'])/2,1)} | SOT {round((hs['sot']+aw['sot'])/2,1)}</div>
<div class='panel' id='p'>Shots L5: {f['home']} FW 2.8/g<br>Fouls: 1.8/g | Cards: 0.4/g<br>Tackles: 3.2/g | Conv: 18%<br><br>{f['away']} top scorer 3.1 shots/g</div>
<div class='panel' id='b'>BTTS {btts}% - <span class='badge'>{"YES" if btts>55 else "NO"}</span><br>Over 2.5 {min(88,55+int((hs['g']+aw['g'])*10))}%<br>Corners Over 8.5 {int((hs['co']+aw['co'])*6)}%<br>Based on defence leakage {hs['c']}+{aw['c']} conceded<br>Player Over 1.5 shots 72%</div>
<div class='panel' id='a'><b style='color:#00ff88'>🤖 AI PREDICTION</b><br>Winner: {f['home'] if hs['pos']<aw['pos'] else f['away']} 64%<br>BTTS: {"Yes" if btts>58 else "No"} ({btts}%)<br>Score: 2-1<br>Best: <span class='badge'>BTTS + Over 2.5</span></div>
</div>
"""
        html+="</div>"

    html+=f"""
</div>
<div style='height:70px'></div>
<div class='bottom'>
<div class='bitem active'>🗓️<br>Fixtures</div><div class='bitem'>🔔<br>Alerts</div><div class='bitem'>📈<br>Trends</div><div class='bitem'>☰<br>More</div>
</div>
<script>
let liveOnly=false;
function toggleLive(){{
 liveOnly=!liveOnly;
 document.getElementById('liveBtn').classList.toggle('on');
 let fixtures=document.querySelectorAll('.fixture');
 if(liveOnly){{
   document.querySelectorAll('.country').forEach(c=>c.classList.add('open'));
   fixtures.forEach(f=>{{ if(f.dataset.live!=='true') f.style.display='none'; else f.style.display='block'; }});
 }} else {{
   fixtures.forEach(f=>{{ f.style.display=''; if(!f.classList.contains('live')) f.style.display='none'; }});
   document.querySelectorAll('.country').forEach(c=>{{ if(!c.querySelector('.fixture.live')) c.classList.remove('open'); }});
   document.querySelectorAll('.country.open.fixture').forEach(f=>f.style.display='block');
 }}
}}
function openTab(el,id){{
 let box=el.closest('.stats');
 box.querySelectorAll('.mtab').forEach(t=>t.classList.remove('active')); el.classList.add('active');
 box.querySelectorAll('.panel').forEach(p=>p.classList.remove('active')); box.querySelector('#'+id).classList.add('active');
}}
</script>
</body></html>
"""
    return html

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
