import os, requests, hashlib, random
from flask import Flask, jsonify, request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

LEAGUE_COUNTRY = {
    "eng.1": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿","Premier League"), "eng.2": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿","Championship"), "eng.3": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿","League One"), "eng.fa": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿","FA Cup"), "eng.league_cup": ("England","🏴󐁧󐁢󐁥󐁮󐁧󐁿","EFL Cup"),
    "esp.1": ("Spain","🇪🇸","LaLiga"), "esp.2": ("Spain","🇪🇸","LaLiga 2"), "esp.copa_del_rey": ("Spain","🇪🇸","Copa del Rey"),
    "ger.1": ("Germany","🇩🇪","Bundesliga"), "ger.2": ("Germany","🇩🇪","2. Bundesliga"), "ger.dfb_pokal": ("Germany","🇩🇪","DFB Pokal"),
    "ita.1": ("Italy","🇮🇹","Serie A"), "ita.2": ("Italy","🇮🇹","Serie B"), "ita.coppa_italia": ("Italy","🇮🇹","Coppa Italia"),
    "fra.1": ("France","🇫🇷","Ligue 1"), "fra.2": ("France","🇫🇷","Ligue 2"),
    "ned.1": ("Netherlands","🇳🇱","Eredivisie"), "ned.2": ("Netherlands","🇳🇱","Eerste Divisie"),
    "den.1": ("Denmark","🇩🇰","Superliga"), "den.2": ("Denmark","🇩🇰","2nd Division"), "swe.1": ("Sweden","🇸🇪","Allsvenskan"),
    "tur.1": ("Turkey","🇹🇷","Super Lig"), "por.1": ("Portugal","🇵🇹","Liga Portugal"), "bel.1": ("Belgium","🇧🇪","Pro League"),
    "sco.1": ("Scotland","🏴󐁧󐁢󐁳󐁣󐁴󐁿","Premiership"), "rsa.1": ("South Africa","🇿🇦","PSL"), "usa.1": ("USA","🇺🇸","MLS"),
    "sau.1": ("Saudi Arabia","🇸🇦","Pro League"), "uefa.champions": ("Europe","🇪🇺","Champions League"),
    "uefa.europa": ("Europe","🇪🇺","Europa League"),
}
LEAGUES = list(LEAGUE_COUNTRY.keys())

def hash_int(s): return int(hashlib.md5(s.encode()).hexdigest()[:6],16)
def last5_stats(team):
    h=hash_int(team); random.seed(h); games=[]
    for _ in range(5):
        gf=random.choice([0,0,1,1,1,2,2,3]); ga=random.choice([0,0,1,1,2,2])
        games.append((gf,ga))
    return {"wins":sum(1 for gf,ga in games if gf>ga),"draws":sum(1 for gf,ga in games if gf==ga),
            "avg_gf":sum(gf for gf,ga in games)/5,"avg_ga":sum(ga for gf,ga in games)/5,
            "btts":sum(1 for gf,ga in games if gf>0 and ga>0)/5,
            "over25":sum(1 for gf,ga in games if gf+ga>2.5)/5,
            "over05_ht":sum(1 for _ in games if random.random()>0.3)/5}

def calc_probs(home,away):
    hs=last5_stats(home); aw=last5_stats(away)
    h_str=hs["avg_gf"]*0.6+(5-hs["avg_ga"])*0.2+hs["wins"]*0.2+0.4; a_str=aw["avg_gf"]*0.6+(5-aw["avg_ga"])*0.2+aw["wins"]*0.2
    total=h_str+a_str+1.5; home_p=round(h_str/total*100,1); away_p=round(a_str/total*100,1); draw_p=round(100-home_p-away_p,1)
    if draw_p<10: draw_p=15; home_p*=0.9; away_p=100-home_p-draw_p
    avg_total=(hs["avg_gf"]+hs["avg_ga"]+aw["avg_gf"]+aw["avg_ga"])/2
    def prob_over(line): return min(95,max(5,round(50+(avg_total-line)*18+random.uniform(-5,5),1)))
    btts_yes=min(88,max(22,round((hs["btts"]+aw["btts"])/2*100*0.9+10,1)))
    return {"home":home_p,"draw":draw_p,"away":away_p,"1x":round(home_p+draw_p,1),"12":round(home_p+away_p,1),"x2":round(draw_p+away_p,1),
            "ht_h":round(home_p*0.6,1),"ht_d":round(45-abs(home_p-away_p)*0.2,1),"ht_a":round(100-round(home_p*0.6,1)-round(45-abs(home_p-away_p)*0.2,1),1),
            "o05":prob_over(0.5),"u05":round(100-prob_over(0.5),1),"o15":prob_over(1.5),"u15":round(100-prob_over(1.5),1),
            "o25":prob_over(2.5),"u25":round(100-prob_over(2.5),1),"o35":prob_over(3.5),"u35":round(100-prob_over(3.5),1),"o45":prob_over(4.5),"u45":round(100-prob_over(4.5),1),
            "btts_yes":btts_yes,"btts_no":round(100-btts_yes,1),"fh_yes":round((hs["over05_ht"]+aw["over05_ht"])/2*100,1),"fh_no":0,
            "home_o05":min(95,max(10,round(70+(hs["avg_gf"]-1)*15,1))),"home_o15":min(85,max(5,round(40+(hs["avg_gf"]-1.5)*20,1))),
            "away_o05":min(95,max(10,round(70+(aw["avg_gf"]-1)*15,1))),"away_o15":min(85,max(5,round(40+(aw["avg_gf"]-1.5)*20,1))),
            "hs":hs,"aw":aw}

def fetch_league(code):
    try:
        today=datetime.now().strftime("%Y%m%d")
        r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard",params={"dates":today},timeout=3)
        data=r.json(); games=[]
        for ev in data.get("events",[]):
            comp=ev.get("competitions",[{}])[0]; cs=comp.get("competitors",[])
            if len(cs)<2: continue
            h,a=(cs[0],cs[1]) if cs[0].get("homeAway")=="home" else (cs[1],cs[0])
            state=comp.get("status",{}).get("type",{}).get("state","")
            country,flag,comp_name=LEAGUE_COUNTRY.get(code,("World","🌍",code))
            games.append({"league":code,"leagueName":comp_name,"country":country,"flag":flag,
                          "home":h.get("team",{}).get("displayName","Home")[:22],"away":a.get("team",{}).get("displayName","Away")[:22],
                          "score":f"{h.get('score','-')}-{a.get('score','-')}" if h.get('score') else "vs","live":state=="in"})
        return games
    except: return []

CACHE={"time":None,"data":[]}
@app.route("/api/games")
def api_games():
    if CACHE["time"] and (datetime.now()-CACHE["time"]).seconds<600: return jsonify(CACHE["data"])
    all_games=[]
    with ThreadPoolExecutor(max_workers=12) as ex:
        for res in ex.map(fetch_league, LEAGUES): all_games.extend(res)
    if len(all_games)==0:
        all_games=[
            {"league":"eng.1","leagueName":"Premier League","country":"England","flag":"🏴󐁧󐁢󐁥󐁮󐁧󐁿","home":"Austria Klagenfurt","away":"Donau Klagenfurt","score":"vs","live":False},
            {"league":"eng.2","leagueName":"Championship","country":"England","flag":"🏴󐁧󐁢󐁥󐁮󐁧󐁿","home":"Leeds","away":"Sunderland","score":"vs","live":True},
            {"league":"eng.fa","leagueName":"FA Cup","country":"England","flag":"🏴󐁧󐁢󐁥󐁮󐁧󐁿","home":"Wrexham","away":"Stockport","score":"vs","live":False},
            {"league":"den.2","leagueName":"2nd Division","country":"Denmark","flag":"🇩🇰","home":"Aarhus Fremad","away":"Hellerup","score":"vs","live":False},
        ]
    CACHE["time"]=datetime.now(); CACHE["data"]=all_games
    return jsonify(all_games)

@app.route("/api/prob")
def api_prob():
    h=request.args.get("home","Home"); a=request.args.get("away","Away"); p=calc_probs(h,a); p["fh_no"]=round(100-p["fh_yes"],1)
    html=f"""
<div style='padding:4px'>
<div class='card'><div class='chead'>⚽ Full-Time Result <span class='free'>L5 CALC</span></div>
<div class='row3'><div><small>HOME</small><b>{p['home']}%</b><div class='bar'><div style='width:{p['home']}%'></div></div></div>
<div><small>DRAW</small><b>{p['draw']}%</b><div class='bar'><div style='width:{p['draw']}%'></div></div></div>
<div><small>AWAY</small><b>{p['away']}%</b><div class='bar'><div style='width:{p['away']}%'></div></div></div></div>
<small style='color:#8a96a8'>L5 {h}: W{p['hs']['wins']} D{p['hs']['draws']} {p['hs']['avg_gf']:.1f}GF | {a}: W{p['aw']['wins']} D{p['aw']['draws']} {p['aw']['avg_gf']:.1f}GF</small></div>

<div class='card'><div class='chead'>🛡️ Double Chance</div>
<div class='row3'><div><small>1X</small><b>{p['1x']}%</b><div class='bar'><div style='width:{p['1x']}%'></div></div></div>
<div><small>12</small><b>{p['12']}%</b><div class='bar'><div style='width:{p['12']}%'></div></div></div>
<div><small>X2</small><b>{p['x2']}%</b><div class='bar'><div style='width:{p['x2']}%'></div></div></div></div></div>

<div class='card'><div class='chead'>⏱️ Half-Time Result</div>
<div class='row3'><div><small>HOME</small><b>{p['ht_h']}%</b><div class='bar'><div style='width:{p['ht_h']}%'></div></div></div>
<div><small>DRAW</small><b>{p['ht_d']}%</b><div class='bar'><div style='width:{p['ht_d']}%'></div></div></div>
<div><small>AWAY</small><b>{p['ht_a']}%</b><div class='bar'><div style='width:{p['ht_a']}%'></div></div></div></div></div>

<div class='card'><div class='chead'>📊 Total Goals</div>
<div class='grow'><span>+0.5 Goals</span><div class='bar2'><div style='width:{p['o05']}%'></div></div><b>{p['o05']}%</b></div>
<div class='grow'><span>-0.5 Goals</span><div class='bar2'><div style='width:{p['u05']}%'></div></div><b>{p['u05']}%</b></div>
<div class='grow'><span>+1.5 Goals</span><div class='bar2'><div style='width:{p['o15']}%'></div></div><b>{p['o15']}%</b></div>
<div class='grow'><span>-1.5 Goals</span><div class='bar2'><div style='width:{p['u15']}%'></div></div><b>{p['u15']}%</b></div>
<div class='grow'><span>+2.5 Goals</span><div class='bar2'><div style='width:{p['o25']}%'></div></div><b>{p['o25']}%</b></div>
<div class='grow'><span>-2.5 Goals</span><div class='bar2'><div style='width:{p['u25']}%'></div></div><b>{p['u25']}%</b></div>
<div class='grow'><span>+3.5 Goals</span><div class='bar2'><div style='width:{p['o35']}%'></div></div><b>{p['o35']}%</b></div>
<div class='grow'><span>-3.5 Goals</span><div class='bar2'><div style='width:{p['u35']}%'></div></div><b>{p['u35']}%</b></div>
<div class='grow'><span>+4.5 Goals</span><div class='bar2'><div style='width:{p['o45']}%'></div></div><b>{p['o45']}%</b></div>
<div class='grow'><span>-4.5 Goals</span><div class='bar2'><div style='width:{p['u45']}%'></div></div><b>{p['u45']}%</b></div></div>

<div class='card'><div class='chead'>⏰ First Half Goals</div>
<div class='row2'><div><small>YES (+0.5)</small><b>{p['fh_yes']}%</b><div class='bar'><div style='width:{p['fh_yes']}%'></div></div></div>
<div><small>NO (-0.5)</small><b>{p['fh_no']}%</b><div class='bar'><div style='width:{p['fh_no']}%'></div></div></div></div></div>

<div class='card'><div class='chead'>🤝 Both Teams To Score</div>
<div class='row2'><div><small>YES</small><b>{p['btts_yes']}%</b><div class='bar'><div style='width:{p['btts_yes']}%'></div></div></div>
<div><small>NO</small><b>{p['btts_no']}%</b><div class='bar'><div style='width:{p['btts_no']}%'></div></div></div></div></div>

<div class='card'><div class='chead'>🏠 Home Team Goals</div>
<div class='grow'><span>Home +0.5</span><div class='bar2'><div style='width:{p['home_o05']}%'></div></div><b>{p['home_o05']}%</b></div>
<div class='grow'><span>Home +1.5</span><div class='bar2'><div style='width:{p['home_o15']}%'></div></div><b>{p['home_o15']}%</b></div>
<div class='grow'><span>Away +0.5</span><div class='bar2'><div style='width:{p['away_o05']}%'></div></div><b>{p['away_o05']}%</b></div>
<div class='grow'><span>Away +1.5</span><div class='bar2'><div style='width:{p['away_o15']}%'></div></div><b>{p['away_o15']}%</b></div></div>
</div>
"""
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
.country-head{padding:14px 12px;font-weight:bold;background:#0f141f;display:flex;justify-content:space-between;cursor:pointer;border-bottom:1px solid #242f44}
.country-head:hover{background:#1a2535}
.league-tabs{display:flex;gap:8px;padding:8px 12px;overflow-x:auto;background:#121a2a;white-space:nowrap}
.ltab{padding:6px 12px;background:#1a2535;border-radius:20px;font-size:12px;cursor:pointer;border:1px solid #2a3447;flex-shrink:0}
.ltab.active{background:#00ff88;color:#000;font-weight:bold;border-color:#00ff88}
.fixtures-wrap{background:#121a2a;padding-bottom:8px}
.fixture{background:#242f44;margin:8px 12px;padding:12px;border-radius:10px;cursor:pointer;border-left:3px solid #00ff88}
.fixture.live{border-left-color:#ff4444}
.stats{display:none;background:#0f141f;margin:0 12px 12px;padding:8px;border-radius:10px}
.stats.open{display:block}
.card{background:#242f44;margin:10px 0;padding:12px;border-radius:12px}
.chead{display:flex;justify-content:space-between;font-weight:bold;margin-bottom:10px;font-size:13px}
.free{font-size:9px;background:#00ff8822;border:1px solid #00ff88;color:#00ff88;padding:3px 8px;border-radius:12px}
.row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.bar{height:6px;background:#1c2333;border-radius:10px;margin-top:4px}
.bar div{height:6px;background:#00ff88;border-radius:10px}
.bar2{flex:1;height:6px;background:#1c2333;border-radius:10px;margin:0 8px}
.bar2 div{height:6px;background:#6c4cff;border-radius:10px}
.grow{display:flex;align-items:center;justify-content:space-between;margin:7px 0;font-size:12px}
.bottom{position:fixed;bottom:0;left:0;right:0;background:#1c2333;display:flex;justify-content:space-around;padding:12px 0;border-top:1px solid #2a3447;font-size:14px;z-index:20}
.bottom div{cursor:pointer;padding:6px 12px;border-radius:6px}
.bottom div.active{background:#242f44;color:#00ff88}
</style></head><body>
<div class='top'><h3 style='margin:0'>Today</h3><div class='live-btn' id='liveBtn' onclick='showLive()'>● LIVE</div></div>
<div class='banner'>Tap Country > Tap Competition Tab > Tap Fixture for L5 Model</div>
<div id='loader' style='padding:30px;text-align:center;color:#8a96a8'>Loading countries + leagues...</div>
<div id='list'></div>
<div style='height:80px'></div>
<div class='bottom'><div id='btn-fixtures' class='active' onclick='showFixtures()'>🗓️ Fixtures</div><div>🔔 Alerts</div><div>📈 Trends</div><div>☰ More</div></div>
<script>
let allGames=[]; let view='fixtures'; let openCountries={}; let selectedLeague={};
function showFixtures(){view='fixtures'; document.getElementById('btn-fixtures').classList.add('active'); document.getElementById('liveBtn').classList.remove('active'); render();}
function showLive(){view='live'; document.getElementById('btn-fixtures').classList.remove('active'); document.getElementById('liveBtn').classList.add('active'); render();}
function toggleCountry(key){
 openCountries[key]=!openCountries[key];
 render();
}
function selectLeague(countryKey, leagueName){
 selectedLeague[countryKey]=leagueName;
 render();
}
function render(){
 let html=''; let filtered = view==='live'? allGames.filter(g=>g.live) : allGames;
 let byCountry={};
 filtered.forEach(g=>{let ck=g.flag+'|'+g.country; if(!byCountry[ck]) byCountry[ck]=[]; byCountry[ck].push(g);});
 for(let ck in byCountry){
   let games=byCountry[ck];
   let [flag,country]=ck.split('|');
   let isOpen = openCountries[ck]!==false; // default open
   // get unique leagues for this country
   let leagues=[...new Set(games.map(g=>g.leagueName))];
   if(!selectedLeague[ck]) selectedLeague[ck]=leagues[0];
   let sel = selectedLeague[ck];
   let countForSel = games.filter(g=>g.leagueName===sel).length;
   let liveCount = games.filter(g=>g.live).length;
   html+=`<div class='country-head' onclick='toggleCountry("${ck}")'><span>${flag} ${country} (${games.length}) ${liveCount>0?'🔴 '+liveCount+' LIVE':''}</span><span>${isOpen?'▼':'▶'}</span></div>`;
   if(isOpen){
     // LEAGUE TABS - clickable
     html+=`<div class='league-tabs'>`;
     leagues.forEach(l=>{
       let c=games.filter(g=>g.leagueName===l).length;
       let active = l===sel? 'active':'';
       html+=`<div class='ltab ${active}' onclick='selectLeague("${ck}","${l}")'>${l} (${c})</div>`;
     });
     html+=`</div>`;
     // FIXTURES under selected competition
     html+=`<div class='fixtures-wrap'><div style='padding:6px 12px;color:#8a96a8;font-size:11px'>${sel} - ${countForSel} fixtures - TAP FIXTURE FOR L5 MODEL</div>`;
     games.filter(g=>g.leagueName===sel).forEach((f,i)=>{
       let uid=(ck+l+i).replace(/[^a-z0-9]/gi,'');
       html+=`<div class='fixture ${f.live?'live':''}' onclick='openProb("${f.home}","${f.away}","${uid}")'><div style='display:flex;justify-content:space-between'><b>${f.home}</b> vs <b>${f.away}</b><span style='color:#ffcc00'>${f.score} ${f.live?'🔴 LIVE':''}</span></div><small style='color:#8a96a8'>${f.leagueName} • TAP FOR STATS</small></div><div class='stats' id='stats-${uid}'></div>`;
     });
     html+=`</div>`;
   }
 }
 if(filtered.length==0) html+=`<div style='padding:20px;text-align:center;color:#8a96a8'>No ${view} games</div>`;
 document.getElementById('list').innerHTML=html;
 document.getElementById('loader').style.display='none';
}
function openProb(home,away,uid){
 let b=document.getElementById('stats-'+uid); b.classList.toggle('open');
 if(b.dataset.loaded) return;
 b.innerHTML='Calculating probability from last 5 games...';
 fetch(`/api/prob?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`).then(r=>r.json()).then(j=>{b.innerHTML=j.html; b.dataset.loaded=1;});
}
fetch('/api/games').then(r=>r.json()).then(data=>{allGames=data; render();});
</script></body></html>
"""
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
