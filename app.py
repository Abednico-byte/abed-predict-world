import os, requests, hashlib
from flask import Flask, jsonify, request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

LEAGUE_COUNTRY = {
    "eng.1": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿"), "eng.2": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿"), "eng.fa": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿"),
    "esp.1": ("Spain","🇪🇸"), "ger.1": ("Germany","🇩🇪"), "ita.1": ("Italy","🇮🇹"),
    "fra.1": ("France","🇫🇷"), "ned.1": ("Netherlands","🇳🇱"),
    "den.1": ("Denmark","🇩🇰"), "den.2": ("Denmark","🇩🇰"), "swe.1": ("Sweden","🇸🇪"),
    "tur.1": ("Turkey","🇹🇷"), "por.1": ("Portugal","🇵🇹"), "bel.1": ("Belgium","🇧🇪"),
    "sco.1": ("Scotland","🏴󐁧󐁢󐁳󐁣󐁴󐁿"), "rsa.1": ("South Africa","🇿🇦"), "usa.1": ("USA","🇺🇸"),
    "sau.1": ("Saudi Arabia","🇸🇦"), "uefa.champions": ("Europe","🇪🇺"),
}
LEAGUES = list(LEAGUE_COUNTRY.keys())

def fetch_league(code):
    try:
        today = datetime.now().strftime("%Y%m%d")
        r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard",
                         params={"dates": today}, timeout=3)
        data = r.json()
        games=[]
        for ev in data.get("events",[]):
            comp=ev.get("competitions",[{}])[0]
            cs=comp.get("competitors",[])
            if len(cs)<2: continue
            h,a = (cs[0],cs[1]) if cs[0].get("homeAway")=="home" else (cs[1],cs[0])
            state=comp.get("status",{}).get("type",{}).get("state","")
            country, flag = LEAGUE_COUNTRY.get(code, ("World","🌍"))
            # OddAlerts style hash stats
            hh=int(hashlib.md5(h.get("team",{}).get("displayName","").encode()).hexdigest()[:3],16)%100
            aa=int(hashlib.md5(a.get("team",{}).get("displayName","").encode()).hexdigest()[:3],16)%100
            games.append({
                "league": code, "leagueName": data.get("leagues",[{}])[0].get("name",code),
                "country": country, "flag": flag,
                "home": h.get("team",{}).get("displayName","Home")[:18],
                "away": a.get("team",{}).get("displayName","Away")[:18],
                "score": f"{h.get('score','-')}-{a.get('score','-')}" if h.get('score') else "vs",
                "live": state=="in",
                "btts": min(92,max(28,50+(hh+aa)//3)),
                "over25": min(90,max(30,45+(hh//2))),
                "alert": "🔥 BTTS UP" if (hh+aa)%3==0 else "📈 Goals Trend" if (hh+aa)%3==1 else "⚠️ Cards Alert",
                "isPro": code in ["eng.1","esp.1","ger.1","ita.1","fra.1","uefa.champions"]
            })
        return games
    except: return []

CACHE={"time":None,"data":[]}
@app.route("/api/games")
def api_games():
    if CACHE["time"] and (datetime.now()-CACHE["time"]).seconds<600:
        return jsonify(CACHE["data"])
    all_games=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        for res in ex.map(fetch_league, LEAGUES):
            all_games.extend(res)
    if len(all_games)==0:
        all_games=[
            {"league":"eng.1","leagueName":"Premier League","country":"England","flag":"🏴󐁧󐁢󐁥󐁮󐁧󐁿","home":"Arsenal","away":"Man City","score":"vs","live":True,"btts":78,"over25":65,"alert":"🔥 BTTS UP","isPro":True},
            {"league":"eng.fa","leagueName":"FA Cup","country":"England","flag":"🏴󐁧󐁢󐁥󐁮󐁧󐁿","home":"Wrexham","away":"Stockport","score":"vs","live":False,"btts":62,"over25":55,"alert":"📈 Goals Trend","isPro":False},
            {"league":"den.2","leagueName":"Danish 2nd Div","country":"Denmark","flag":"🇩🇰","home":"Aarhus Fremad","away":"Hellerup","score":"vs","live":True,"btts":84,"over25":71,"alert":"⚠️ Cards Alert","isPro":False},
        ]
    CACHE["time"]=datetime.now(); CACHE["data"]=all_games
    return jsonify(all_games)

@app.route("/api/stats")
def api_stats():
    h=request.args.get("home","Home"); a=request.args.get("away","Away")
    hs=int(hashlib.md5(h.encode()).hexdigest()[:5],16); aw=int(hashlib.md5(a.encode()).hexdigest()[:5],16)
    btts=min(85,max(30,55+(hs%20)+(aw%15)-15))
    html=f"""<div><span class='mtab active' onclick='openTab(this,"g")'>General</span><span class='mtab' onclick='openTab(this,"h")'>H2H</span><span class='mtab' onclick='openTab(this,"p")'>Players</span><span class='mtab' onclick='openTab(this,"b")'>Best Bets %</span><span class='mtab' onclick='openTab(this,"ai")'>AI</span></div>
<div class='panel active' id='g'>Goals: {h} {0.8+(hs%15)/10} | {a} {0.8+(aw%15)/10}<br>Fouls 12.5 | SOT 4.2 | Corners 5.1</div>
<div class='panel' id='h'>Pos #{(hs%18)+1} vs #{(aw%18)+1} | BTTS History 60%</div>
<div class='panel' id='p'>Shots L5 2.8/g | Fouls 1.8/g | Cards 0.4/g</div>
<div class='panel' id='b'>BTTS {btts}% YES<br>Over 2.5 {btts+7}%<br>Over 8.5 Corners 65%</div>
<div class='panel' id='ai'><b style='color:#00ff88'>AI PREDICTION</b><br>Winner: {h if hs>aw else a} 62% | BTTS {btts}%</div>"""
    return jsonify({"html":html})

@app.route("/")
def home():
    return """
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{margin:0;background:#1c2333;color:#fff;font-family:Arial}
.top{padding:12px;display:flex;justify-content:space-between;align-items:center;background:#1c2333;position:sticky;top:0;z-index:10}
.live-btn{background:#2a3447;padding:6px 14px;border-radius:20px;font-size:12px;cursor:pointer}
.live-btn.active{background:#ff4444;color:#fff}
.banner{background:#6c4cff;padding:8px 12px;font-size:13px}
.tabs{display:flex;gap:18px;padding:10px 12px;color:#8a96a8;font-size:14px;border-bottom:1px solid #2a3447}
.tab{cursor:pointer}.tab.on{color:#fff;font-weight:bold;border-bottom:2px solid #00ff88}
.section{padding:12px;font-weight:bold;background:#0f141f;display:flex;justify-content:space-between;border-bottom:1px solid #242f44}
.fixture{background:#242f44;margin:8px 12px;padding:12px;border-radius:10px;cursor:pointer;border-left:3px solid #00ff88}
.fixture.live{border-left-color:#ff4444}
.fixture.cup{border-left-color:#ffaa00}
.oddalerts{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.badge{font-size:10px;padding:3px 7px;border-radius:12px;background:#1a2535;border:1px solid #2a3a55}
.badge.hot{background:#ff444422;border-color:#ff4444;color:#ff8888}
.badge.green{background:#00ff8822;border-color:#00ff88;color:#00ff88}
.badge.yellow{background:#ffaa0022;border-color:#ffaa00;color:#ffcc66}
.stats{display:none;background:#0f141f;margin:0 12px 10px;padding:10px;border-radius:10px;font-size:12px}
.stats.open{display:block}
.mtab{display:inline-block;padding:5px 9px;background:#1a2535;border-radius:15px;font-size:11px;margin:3px;cursor:pointer}
.mtab.active{background:#00ff88;color:#000}
.panel{display:none;margin-top:8px;background:#121a2a;padding:10px;border-radius:8px}
.panel.active{display:block}
.bottom{position:fixed;bottom:0;left:0;right:0;background:#1c2333;display:flex;justify-content:space-around;padding:12px 0;border-top:1px solid #2a3447;font-size:14px;z-index:20}
.bottom div{cursor:pointer;padding:6px 12px;border-radius:6px}
.bottom div.active{background:#242f44;color:#00ff88}
</style></head><body>
<div class='top'><h3 style='margin:0'>Today</h3><div class='live-btn' id='liveBtn' onclick='showLive()'>● LIVE</div></div>
<div class='banner'>Enhanced Site-Wide Search Now Live - 21 Sep 2026</div>
<div class='tabs'><span class='tab on' id='tab-hot' onclick='setTab("hot")'>🔥 Hot</span><span class='tab' onclick='setTab("saved")'>⭐ Saved</span><span class='tab' onclick='setTab("alerts")'>🔔 Alerts</span></div>
<div id='loader' style='padding:30px;text-align:center;color:#8a96a8'>Loading OddAlerts style fixtures...</div>
<div id='list'></div>
<div style='height:80px'></div>
<div class='bottom'><div id='btn-fixtures' class='active' onclick='showFixtures()'>🗓️ Fixtures</div><div>🔔 Alerts</div><div>📈 Trends</div><div>☰ More</div></div>
<script>
let allGames=[]; let view='fixtures'; let hotTab='hot';
function showFixtures(){view='fixtures'; document.getElementById('btn-fixtures').classList.add('active'); document.getElementById('liveBtn').classList.remove('active'); render();}
function showLive(){view='live'; document.getElementById('btn-fixtures').classList.remove('active'); document.getElementById('liveBtn').classList.add('active'); render();}
function setTab(t){hotTab=t; document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on')); document.getElementById('tab-'+t)?.classList.add('on'); if(t!=='hot'){document.getElementById('tab-hot').classList.add('on')} render();}
function render(){
 let html='';
 let filtered = view==='live'? allGames.filter(g=>g.live) : allGames;
 // OddAlerts style sorting for Hot
 if(hotTab==='hot' && view!=='live') filtered = [...filtered].sort((a,b)=>b.btts-a.btts);
 let groups={};
 filtered.forEach(g=>{
   let key = g.flag+' '+g.country;
   if(!groups[key]) groups[key]=[];
   groups[key].push(g);
 });
 for(let country in groups){
   let gl=groups[country];
   html+=`<div class='section'><span>${country} (${gl.length})</span><span style='color:#8a96a8'>›</span></div>`;
   gl.forEach((f,i)=>{
     let uid = (country+i).replace(/[^a-z0-9]/gi,'');
     html+=`<div class='fixture ${f.live?'live':''} ${f.isPro?'':'cup'}'>
       <div style='display:flex;justify-content:space-between' onclick='openStats("${f.home}","${f.away}","${uid}")'><b>${f.home}</b> vs <b>${f.away}</b><span style='color:#ffcc00'>${f.score} ${f.live?'🔴 LIVE':''}</span></div>
       <small style='color:#8a96a8'>${f.leagueName}</small>
       <div class='oddalerts'>
         <span class='badge hot'>${f.alert}</span>
         <span class='badge green'>BTTS ${f.btts}%</span>
         <span class='badge yellow'>O 2.5 ${f.over25}%</span>
         <span class='badge' style='color:#8a96a8'>TAP FOR STATS</span>
       </div>
     </div><div class='stats' id='stats-${uid}'></div>`;
   });
 }
 if(filtered.length==0) html+=`<div style='padding:20px;text-align:center;color:#8a96a8'>No ${view} games</div>`;
 document.getElementById('list').innerHTML=html;
 document.getElementById('loader').style.display='none';
}
function openStats(home,away,uid){
 let b=document.getElementById('stats-'+uid);
 b.classList.toggle('open');
 if(b.dataset.loaded) return;
 b.innerHTML='Loading stats...';
 fetch(`/api/stats?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`).then(r=>r.json()).then(j=>{b.innerHTML=j.html; b.dataset.loaded=1;});
}
function openTab(el,id){let box=el.closest('.stats'); box.querySelectorAll('.mtab').forEach(t=>t.classList.remove('active')); el.classList.add('active'); box.querySelectorAll('.panel').forEach(p=>p.classList.remove('active')); box.querySelector('#'+id).classList.add('active');}
fetch('/api/games').then(r=>r.json()).then(data=>{allGames=data; render();});
</script></body></html>
"""
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
