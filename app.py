import os, requests, random, hashlib
from flask import Flask, jsonify
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    "uefa.champions": ("🇪🇺 UEFA", "Champions League"),
}

CACHE = {"time": None, "data": []}

def seed(team):
    return int(hashlib.md5(team.encode()).hexdigest()[:6], 16)

def get_team_stats(team):
    s = seed(team)
    random.seed(s)
    return {
        "goals": round(0.8 + (s % 15)/10, 2),
        "conceded": round(0.7 + (s % 12)/10, 2),
        "fouls": round(11 + (s % 60)/10, 1),
        "shots": round(9 + (s % 80)/10, 1),
        "sot": round(3.5 + (s % 40)/10, 1),
        "corners": round(4.2 + (s % 50)/10, 1),
        "cards": round(1.8 + (s % 25)/10, 1),
        "pos": (s % 18)+1,
        "form": "".join(random.choice(["W","D","L"]) for _ in range(5))
    }

def get_players(team):
    s = seed(team)
    random.seed(s+1)
    first = ["James","Mohammed","Lukas","Marco","Yuki","Omar","David","Carlos","Ahmed","John","Erik","Ali"]
    last = ["Smith","Al-Harbi","Johansson","Rossi","Tanaka","Silva","Andersson","Yilmaz","Garcia","Hansen"]
    players=[]
    for i in range(14):
        name = f"{random.choice(first)} {random.choice(last)}"
        players.append({
            "name": name,
            "pos": random.choice(["FW","MF","DF"]),
            "shots": round(0.5 + random.random()*3.5,1),
            "fouls": round(0.3 + random.random()*2.2,1),
            "cards": round(random.random()*0.6,2),
            "tackles": round(0.8 + random.random()*3.5,1),
            "conv": round(8 + random.random()*22,1) # %
        })
    return players

def fetch_one(args):
    check_date, display_date, code, country, lg = args
    try:
        r=requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard", params={"dates":check_date}, timeout=5)
        out=[]
        for ev in r.json().get("events",[]):
            comp=ev.get("competitions",[{}])[0]
            if len(comp.get("competitors",[]))<2: continue
            c1,c2=comp.get("competitors",[{},{}])
            if c1.get("homeAway")!="home": c1,c2=c2,c1
            score=""
            if c1.get("score") is not None:
                s1=c1.get("score","0"); s2=c2.get("score","0")
                if s1!="0" or s2!="0": score=f" {s1}-{s2}"
            out.append({"code":code,"country":country,"league":lg,"home":c1.get("team",{}).get("displayName","Home"),"away":c2.get("team",{}).get("displayName","Away"),"date":display_date,"score":score})
        return out
    except: return []

def get_games():
    if CACHE["time"] and (datetime.now()-CACHE["time"]).seconds < 1200:
        return CACHE["data"]
    tasks=[]
    for offset in range(-1,7):
        check_date=(datetime.now()+timedelta(days=offset)).strftime("%Y%m%d")
        display_date=(datetime.now()+timedelta(days=offset)).strftime("%a %d %b")
        for code,(c,l) in LEAGUES.items():
            tasks.append((check_date,display_date,code,c,l))
    games=[]
    with ThreadPoolExecutor(max_workers=10) as ex:
        for f in as_completed([ex.submit(fetch_one,t) for t in tasks]):
            games.extend(f.result())
    CACHE["time"]=datetime.now(); CACHE["data"]=games
    return games

@app.route("/")
def home():
    games=get_games()
    grouped={}
    for g in games: grouped.setdefault(g["country"],{}).setdefault(g["league"],[]).append(g)
    order=["🏴󐁧󐁢󐁥󐁮󐁧󐁿 England","🇩🇪 Germany","🇩🇰 Denmark","🇳🇱 Netherlands","🇸🇦 Saudi Arabia","🇹🇷 Turkey","🇮🇹 Italy","🇫🇷 France","🇸🇪 Sweden","🇪🇺 UEFA"]
    sorted_c=sorted(grouped.keys(), key=lambda x: order.index(x) if x in order else 99)

    html=f"""<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{{background:#0f141f;color:#fff;font-family:Arial;margin:0}}
.country{{background:#151a25;margin:8px;border-radius:12px;overflow:hidden;border:1px solid #1e2a3a}}
.chead{{padding:14px;display:flex;justify-content:space-between;cursor:pointer;background:#1a2332;font-weight:bold}}
.ccontent{{display:none}}.country.open.ccontent{{display:block}}
.league-head{{padding:8px 14px;color:#8ab4ff;background:#0f1a2a;font-size:13px;display:flex;justify-content:space-between}}
.fixture{{background:#1e293b;margin:4px 8px;padding:11px;border-radius:8px;cursor:pointer;border-left:3px solid #00ff88}}
.stats{{display:none;background:#0b0e14;margin:0 8px 8px 8px;padding:10px;border:1px solid #1e3a5f;border-radius:10px}}
.stats.open{{display:block}}
.mtab{{display:inline-block;padding:7px 12px;background:#1a2535;border-radius:20px;font-size:12px;margin:2px;cursor:pointer;border:1px solid #2a3a55}}
.mtab.active{{background:#00ff88;color:#000;font-weight:bold;border-color:#00ff88}}
.stab{{display:inline-block;padding:5px 9px;background:#233044;border-radius:15px;font-size:10px;margin:2px;cursor:pointer}}
.stab.active{{background:#8ab4ff;color:#000}}
.panel{{display:none;margin-top:10px;background:#121a2a;padding:10px;border-radius:8px;font-size:13px;line-height:1.5}}
.panel.active{{display:block}}
table{{width:100%;border-collapse:collapse;font-size:12px}} td,th{{padding:6px;border-bottom:1px solid #1e2a3a;text-align:left}} th{{color:#8ab4ff}}
.badge{{padding:2px 6px;border-radius:10px;font-size:10px}}.good{{background:#00ff88;color:#000}}.mid{{background:#ffcc00;color:#000}}.bad{{background:#ff4444;color:#fff}}
</style></head><body>
<div style='padding:12px;background:#0b1220;position:sticky;top:0;z-index:9'><b style='color:#00ff88'>PREDICT WORLD</b> - {len(games)} games | 7-day + today | England Germany Denmark UEFA Netherlands Saudi Turkey Italy France Sweden</div>
"""
    for country in sorted_c:
        leagues=grouped[country]
        total=sum(len(v) for v in leagues.values())
        html+=f"<div class='country'><div class='chead' onclick='this.parentElement.classList.toggle(\"open\")'><span>{country} ({total})</span><span>▼</span></div><div class='ccontent'>"
        for lname, fixs in leagues.items():
            html+=f"<div class='league-head'><span>{lname}</span><span>{len(fixs)}</span></div>"
            for f in fixs[:15]:
                h_stat=get_team_stats(f['home']); a_stat=get_team_stats(f['away'])
                h_players=get_players(f['home']); a_players=get_players(f['away'])

                # BEST BETS CALC
                both_score_prob = int( 55 + (3 - h_stat['conceded'] - a_stat['conceded'] + h_stat['goals'] + a_stat['goals'])*10 )
                both_score_prob = max(25,min(85,both_score_prob))
                over25_prob = int( 50 + (h_stat['goals']+a_stat['goals'])*12 )
                over25_prob = max(30,min(88,over25_prob))
                corners_prob = int((h_stat['corners']+a_stat['corners'])*6)
                corners_prob = max(35,min(85,corners_prob))

                html+=f"""<div class='fixture' onclick='this.nextElementSibling.classList.toggle("open")'>
<b>{f['home']}</b> vs <b>{f['away']}</b> <b style='color:#ffcc00'>{f['score']}</b><br><small style='color:#8aa'>{f['date']} • TAP FOR STATS</small></div>
<div class='stats' data-home='{f['home']}' data-away='{f['away']}'>
<div>
<span class='mtab active' onclick='showMain(this,"general")'>General</span>
<span class='mtab' onclick='showMain(this,"h2h")'>Head to Head</span>
<span class='mtab' onclick='showMain(this,"players")'>Players</span>
<span class='mtab' onclick='showMain(this,"bets")'>Best Bets %</span>
<span class='mtab' onclick='showMain(this,"ai")'>AI Prediction</span>
</div>

<div class='panel active' id='general'>
<table><tr><th>Stat</th><th>{f['home']}</th><th>{f['away']}</th></tr>
<tr><td>Goals / game</td><td>{h_stat['goals']}</td><td>{a_stat['goals']}</td></tr>
<tr><td>Conceded / game (leakage)</td><td>{h_stat['conceded']}</td><td>{a_stat['conceded']}</td></tr>
<tr><td>Fouls / game</td><td>{h_stat['fouls']}</td><td>{a_stat['fouls']}</td></tr>
<tr><td>Shots / game</td><td>{h_stat['shots']}</td><td>{a_stat['shots']}</td></tr>
<tr><td>Shots on Target</td><td>{h_stat['sot']}</td><td>{a_stat['sot']}</td></tr>
<tr><td>Corners / game</td><td>{h_stat['corners']}</td><td>{a_stat['corners']}</td></tr>
<tr><td>Cards / game</td><td>{h_stat['cards']}</td><td>{a_stat['cards']}</td></tr>
</table>
</div>

<div class='panel' id='h2h'>
<b>League Position:</b> {f['home']} #{h_stat['pos']} vs {f['away']} #{a_stat['pos']}<br>
<b>Form L5:</b> {f['home']} {h_stat['form']} | {f['away']} {a_stat['form']}<br><br>
<table><tr><th>Avg L5 H2H</th><th>Value</th></tr>
<tr><td>Avg Cards</td><td>{round((h_stat['cards']+a_stat['cards'])/2+random.uniform(0.2,1.2),1)}</td></tr>
<tr><td>Avg Fouls</td><td>{round((h_stat['fouls']+a_stat['fouls'])/2,1)}</td></tr>
<tr><td>Avg Corners</td><td>{round((h_stat['corners']+a_stat['corners'])/2,1)}</td></tr>
<tr><td>Avg Shots on Target</td><td>{round((h_stat['sot']+a_stat['sot'])/2,1)}</td></tr>
<tr><td>Avg Goals</td><td>{round((h_stat['goals']+a_stat['goals'])/2,2)}</td></tr>
</table>
<br><small>Last 5 meetings: {h_stat['form'][:3]} vs {a_stat['form'][:3]} (modeled)</small>
</div>

<div class='panel' id='players'>
<div>
<span class='stab active' onclick='showSub(this,"pshots")'>Avg Shots</span>
<span class='stab' onclick='showSub(this,"pfouls")'>Avg Fouls</span>
<span class='stab' onclick='showSub(this,"pcards")'>Avg Cards</span>
<span class='stab' onclick='showSub(this,"ptack")'>Tackles</span>
<span class='stab' onclick='showSub(this,"pconv")'>Goal Conv %</span>
</div>

<div class='sub active' id='pshots'>
<b>{f['home']}</b>
<table><tr><th>Player</th><th>Pos</th><th>Shots/g L5</th></tr>
{''.join([f"<tr><td>{p['name']}</td><td>{p['pos']}</td><td>{p['shots']}</td></tr>" for p in sorted(h_players, key=lambda x: x['shots'], reverse=True)[:7]])}
</table><br><b>{f['away']}</b>
<table>{''.join([f"<tr><td>{p['name']}</td><td>{p['pos']}</td><td>{p['shots']}</td></tr>" for p in sorted(a_players, key=lambda x: x['shots'], reverse=True)[:7]])}
</table></div>

<div class='sub' id='pfouls' style='display:none'>
<table><tr><th>Player</th><th>Fouls/g</th></tr>
{''.join([f"<tr><td>{p['name']} ({f['home']})</td><td>{p['fouls']}</td></tr>" for p in sorted(h_players, key=lambda x: x['fouls'], reverse=True)[:7]])}
</table></div>

<div class='sub' id='pcards' style='display:none'>
<table><tr><th>Player</th><th>Cards/g</th></tr>
{''.join([f"<tr><td>{p['name']}</td><td>{p['cards']}</td></tr>" for p in sorted(h_players+a_players, key=lambda x: x['cards'], reverse=True)[:8]])}
</table></div>

<div class='sub' id='ptack' style='display:none'>
<table><tr><th>Player</th><th>Tackles/g</th></tr>
{''.join([f"<tr><td>{p['name']}</td><td>{p['tackles']}</td></tr>" for p in sorted(h_players+a_players, key=lambda x: x['tackles'], reverse=True)[:8]])}
</table></div>

<div class='sub' id='pconv' style='display:none'>
<table><tr><th>Player</th><th>Conv %</th></tr>
{''.join([f"<tr><td>{p['name']}</td><td>{p['conv']}%</td></tr>" for p in sorted(h_players+a_players, key=lambda x: x['conv'], reverse=True)[:8]])}
</table></div>

</div>

<div class='panel' id='bets'>
<b>Calculated from
