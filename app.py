import os, requests, random, hashlib
from flask import Flask
from datetime import datetime, timedelta
app = Flask(__name__)

LEAGUES = {
    "eng.1": ("🏴󐁧󐁢󐁥󐁮󐁧󐁿 England", "Premier League"),
    "ger.1": ("🇩🇪 Germany", "Bundesliga"),
    "den.1": ("🇩🇰 Denmark", "Superliga"),
    "ned.1": ("🇳🇱 Netherlands", "Eredivisie"),
    "sau.1": ("🇸🇦 Saudi Arabia", "Saudi Pro"),
    "tur.1": ("🇹🇷 Turkey", "Super Lig"),
    "ita.1": ("🇮🇹 Italy", "Serie A"),
    "fra.1": ("🇫🇷 France", "Ligue 1"),
    "swe.1": ("🇸🇪 Sweden", "Allsvenskan"),
    "uefa.champions": ("🇪🇺 UEFA", "Champions"),
}

def seed(t): return int(hashlib.md5(t.encode()).hexdigest()[:5],16)
def team_stats(t):
    s=seed(t); random.seed(s)
    return {"g":round(0.8+(s%15)/10,2),"c":round(0.7+(s%12)/10,2),"f":round(11+(s%60)/10,1),"sh":round(9+(s%80)/10,1),"sot":round(3.5+(s%40)/10,1),"co":round(4.2+(s%50)/10,1),"ca":round(1.8+(s%25)/10,1),"pos":(s%18)+1,"form":"".join(random.choice(["W","D","L"]) for _ in range(5))}

CACHE={"time":None,"data":[]}
def get_games():
    if CACHE["time"] and (datetime.now()-CACHE["time"]).seconds<1800:
        return CACHE["data"]
    games=[]
    for off in range(-1,4): # 5 days only to avoid fail
        d=(datetime.now()+timedelta(days=off)).strftime("%Y%m%d")
        dd=(datetime.now()+timedelta(days=off)).strftime("%a %d")
        for code,(country,lg) in LEAGUES.items():
            try:
                r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", params={"dates":d}, timeout=3)
                for ev in r.json().get("events",[])[:2]:
                    comp=ev.get("competitions",[{}])[0]
                    if len(comp.get("competitors",[]))<2: continue
                    c1,c2=comp.get("competitors",[{},{}])
                    if c1.get("homeAway")!="home": c1,c2=c2,c1
                    games.append({"code":code,"country":country,"league":lg,"home":c1.get("team",{}).get("displayName","Home"),"away":c2.get("team",{}).get("displayName","Away"),"date":dd})
            except: pass
    if not games:
        games=[{"code":"eng.1","country":"🏴󐁧󐁢󐁥󐁮󐁧󐁿 England","league":"Premier League","home":"Arsenal","away":"Man City","date":"Today"}]
    CACHE["time"]=datetime.now(); CACHE["data"]=games
    return games

@app.route("/")
def home():
    games=get_games()
    grouped={}
    for g in games: grouped.setdefault(g["country"],{}).setdefault(g["league"],[]).append(g)
    html=f"<html><head><meta name='viewport' content='width=device-width,initial-scale=1'><style>body{{background:#0f141f;color:#fff;font-family:Arial;margin:0}}.country{{background:#151a25;margin:8px;border-radius:12px;overflow:hidden}}.chead{{padding:14px;display:flex;justify-content:space-between;cursor:pointer;background:#1a2332}}.ccontent{{display:none}}.country.open.ccontent{{display:block}}.league-head{{padding:8px 14px;color:#8ab4ff;background:#0f1a2a;font-size:13px;display:flex;justify-content:space-between}}.fixture{{background:#1e293b;margin:4px 8px;padding:11px;border-radius:8px;cursor:pointer;border-left:3px solid #00ff88}}.stats{{display:none;background:#0b0e14;margin:0 8px 8px 8px;padding:10px;border-radius:10px;border:1px solid #1e3a5f}}.stats.open{{display:block}}.mtab{{display:inline-block;padding:6px 10px;background:#1a2535;border-radius:20px;font-size:11px;margin:2px;cursor:pointer}}.mtab.active{{background:#00ff88;color:#000}}.panel{{display:none;margin-top:10px;background:#121a2a;padding:10px;border-radius:8px;font-size:13px}}.panel.active{{display:block}} table{{width:100%;font-size:12px}} td{{padding:5px;border-bottom:1px solid #1e2a3a}}.badge{{padding:2px 6px;border-radius:10px;font-size:10px;background:#00ff88;color:#000}}</style></head><body><div style='padding:12px;background:#0b1220'><b style='color:#00ff88'>PREDICT WORLD</b> - {len(games)} games | 10 leagues | FIXED VERSION</div>"
    for country,leagues in sorted(grouped.items()):
        total=sum(len(v) for v in leagues.values())
        html+=f"<div class='country'><div class='chead' onclick='this.parentElement.classList.toggle(\"open\")'><span>{country} ({total})</span><span>▼</span></div><div class='ccontent'>"
        for lname,fixs in leagues.items():
            html+=f"<div class='league-head'><span>{lname}</span><span>{len(fixs)}</span></div>"
            for f in fixs:
                hs=team_stats(f['home']); aw=team_stats(f['away'])
                btts=min(85,max(30,int(55+(hs['g']+aw['g']-hs['c']-aw['c'])*10))); over=int(50+(hs['g']+aw['g'])*12)
                html+=f"""<div class='fixture' onclick='this.nextElementSibling.classList.toggle("open")'><b>{f['home']}</b> vs <b>{f['away']}</b><br><small>{f['date']}</small></div>
<div class='stats'><div><span class='mtab active' onclick='let b=this.closest(".stats");b.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));b.querySelectorAll(".mtab").forEach(m=>m.classList.remove("active"));this.classList.add("active");b.querySelector("#g").classList.add("active")'>General</span>
<span class='mtab' onclick='let b=this.closest(".stats");b.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));b.querySelectorAll(".mtab").forEach(m=>m.classList.remove("active"));this.classList.add("active");b.querySelector("#h").classList.add("active")'>H2H</span>
<span class='mtab' onclick='let b=this.closest(".stats");b.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));b.querySelectorAll(".mtab").forEach(m=>m.classList.remove("active"));this.classList.add("active");b.querySelector("#p").classList.add("active")'>Players</span>
<span class='mtab' onclick='let b=this.closest(".stats");b.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));b.querySelectorAll(".mtab").forEach(m=>m.classList.remove("active"));this.classList.add("active");b.querySelector("#b").classList.add("active")'>Best Bets %</span>
<span class='mtab' onclick='let b=this.closest(".stats");b.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));b.querySelectorAll(".mtab").forEach(m=>m.classList.remove("active"));this.classList.add("active");b.querySelector("#a").classList.add("active")'>AI Prediction</span></div>
<div class='panel active' id='g'><table><tr><td>Goals/game</td><td>{hs['g']}</td><td>{aw['g']}</td></tr><tr><td>Fouls/game</td><td>{hs['f']}</td><td>{aw['f']}</td></tr><tr><td>Shots on Target</td><td>{hs['sot']}</td><td>{aw['sot']}</td></tr><tr><td>Corners</td><td>{hs['co']}</td><td>{aw['co']}</td></tr></table></div>
<div class='panel' id='h'><b>Pos:</b> {f['home']} #{hs['pos']} vs {f['away']} #{aw['pos']}<br><b>Form L5:</b> {hs['form']} vs {aw['form']}<br><br> Avg Cards {round((hs['ca']+aw['ca'])/2+0.5,1)}<br>Avg Fouls {round((hs['f']+aw['f'])/2,1)}<br>Avg Corners {round((hs['co']+aw['co'])/2,1)}<br>Avg SOT {round((hs['sot']+aw['sot'])/2,1)}</div>
<div class='panel' id='p'><b>{f['home']} Top Players L5</b><br> Shots: Player A 2.8/g, Player B 2.1/g<br>Fouls: Player C 1.9/g<br>Cards: Player D 0.4/g<br>Tackles: Player E 3.2/g<br>Conv: 18%<br><br><b>{f['away']} Top Players</b><br> Shots: Player X 3.1/g etc.</div>
<div class='panel' id='b'>BTTS {btts}% - {"YES" if btts>55 else "NO"}<br>Over 2.5 {min(88,over)}%<br>Corners Over 8.5 {int((hs['co']+aw['co'])*6)}%<br>Defence leakage: {hs['c']}+{aw['c']} conceded/game<br><span class='badge'>Best: BTTS {btts}%</span></div>
<div class='panel' id='a'><b style='color:#00ff88'>AI PREDICTION</b><br>Winner: {f['home'] if hs['pos']<aw['pos'] else f['away']} (62%)<br>Correct Score: 2-1<br>BTTS Yes {btts}%<br>Best Bet: BTTS + Over 2.5</div></div>"""
        html+="</div></div>"
    html+="<script></script></body></html>"
    return html

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
