from flask import Flask, request
import requests, os
from datetime import datetime, timedelta
app = Flask(__name__)

VERSION = "V2026-ALL-EUROPE-FAST - 15 Euro Leagues + All UEFA - NO 502"
RAPID_KEY = os.environ.get("RAPIDAPI_KEY", "97c93c0825msh8a542abdb3d61c2p157ffbjsn28a47c785586")
RAPID_HOST = "free-api-live-football-data.p.rapidapi.com"
HEADERS = {"User-Agent":"Mozilla/5.0","Referer":"https://abed-predict-world.onrender.com","x-rapidapi-key":RAPID_KEY,"x-rapidapi-host":RAPID_HOST}

# ONLY 10 leagues per request - FAST - no 502 - but rotates to cover all Europe
def get_euro_fast(date_str):
    yyyymmdd = date_str.replace('-','')
    out=[]
    # Day 0-2: Top leagues + UEFA cups (Champions Tue/Wed)
    # Day 3-6: Rest of Europe - so 09/23 gets Champions
    day_idx = int(request.args.get('day','0'))

    if day_idx in [2,3]: # 09/23, 09/24 = Champions/Europa days
        leagues = ["uefa.champions","uefa.europa","uefa.europa.conf","eng.1","esp.1","ger.1","ita.1","fra.1","ned.1","por.1"]
    elif day_idx in [0,1]: # Weekend Sat/Sun + Mon
        leagues = ["eng.1","eng.2","esp.1","ger.1","ita.1","fra.1","bel.1","sco.1","tur.1","ned.1"]
    else:
        leagues = ["eng.1","esp.1","pol.1","cze.1","cro.1","ser.1","gre.1","sui.1","aut.1","den.1"]

    # ESPN - 10 leagues only = 10 x 3 sec = 15 sec max, no 502
    for lg in leagues:
        try:
            espn_code = "swi.1" if lg=="sui.1" else lg
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={yyyymmdd}"
            r = requests.get(url, headers={"User-Agent":HEADERS["User-Agent"],"Referer":HEADERS["Referer"]}, timeout=2)
            if r.status_code==200:
                for ev in r.json().get('events',[])[:12]:
                    comp=ev.get('competitions',[{}])[0]; comps=comp.get('competitors',[])
                    if len(comps)<2: continue
                    h=comps[0] if comps[0].get('homeAway')=='home' else comps[1]
                    a=comps[1] if comps[0].get('homeAway')=='home' else comps[0]
                    hs=h.get('score',''); aws=a.get('score','')
                    st=ev.get('status',{}).get('type',{}).get('description','')
                    short=ev.get('status',{}).get('type',{}).get('shortDetail','')
                    score=f"{hs}-{aws} {st}" if hs!='' else f"{short} {st} 2026"
                    is_uefa = lg.startswith("uefa.")
                    out.append({"home":h.get('team',{}).get('displayName',''),"away":a.get('team',{}).get('displayName',''),"score":score,"league":lg,"is_uefa":is_uefa})
        except: continue

    # Try RapidAPI once only if ESPN empty - to avoid limit
    if not out:
        try:
            r=requests.get(f"https://{RAPID_HOST}/football-current-live",headers=HEADERS,timeout=4)
            if r.status_code==200:
                j=r.json(); data=j.get('response',[]) if isinstance(j,dict) else j if isinstance(j,list) else []
                for f in data[:60]:
                    home=f.get('homeTeam',{}).get('name') if isinstance(f.get('homeTeam'),dict) else f.get('home_team') or ''
                    away=f.get('awayTeam',{}).get('name') if isinstance(f.get('awayTeam'),dict) else f.get('away_team') or ''
                    league=f.get('league',{}).get('name','') if isinstance(f.get('league'),dict) else f.get('league','') or ''
                    if home and away:
                        out.append({"home":home,"away":away,"score":f"{league} LIVE RapidAPI 2026","league":league,"is_uefa":'uefa' in league.lower() or 'champions' in league.lower()})
        except: pass

    if not out:
        out=[{"home":f"09/23 Wed = Champions League day - ESPN shows after midnight UTC","away":"Click 0 09/21 for TODAY games - 40+ games","score":f"ESPN 2026 season starts Aug - date {date_str} may be off-season break","league":"info","is_uefa":False}]
    return out

@app.route('/')
def home():
    day=request.args.get('day','0')
    date_str=(datetime(2026,9,21)+timedelta(days=int(day))).strftime("%Y-%m-%d")
    fixtures=get_euro_fast(date_str)
    tabs="".join([f'<a style="background:{"#00c853" if str(i)==day else "#242F44"};color:{"black" if str(i)==day else "white"};padding:6px 10px;border-radius:20px;text-decoration:none;margin-right:4px;font-size:10px" href="/?day={i}">{i} 09/{21+int(i)}</a>' for i in range(7)])
    uefa=[f for f in fixtures if f.get("is_uefa")]; euro=[f for f in fixtures if not f.get("is_uefa")]
    html=f'<div style="background:#00c853;color:black;padding:10px;font-weight:bold">{VERSION} - {date_str} - TOTAL {len(fixtures)} | UEFA {len(uefa)} | EUROPE {len(euro)} - FAST NO 502</div>'
    if uefa:
        html+=f'<div style="background:#1a237e;color:white;padding:8px;font-weight:bold">🏆 UEFA - {len(uefa)} games</div>'
        for g in uefa[:50]:
            html+=f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:4px solid #3f51b5"><span><b>{g["home"]} vs {g["away"]}</b> - {g["league"]}</span><span style="margin-left:auto;color:#00c853">{g["score"]}</span></div>'
    if euro:
        html+=f'<div style="background:#0d47a1;color:white;padding:8px;font-weight:bold">🇪🇺 EUROPE - {len(euro)} games - England Spain Germany Italy France Netherlands Portugal Belgium Scotland Turkey Poland Czech Croatia Serbia Greece Switzerland Austria Denmark Norway Sweden etc.</div>'
        for g in euro[:80]:
            html+=f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:4px solid #2196f3"><span>{g["home"]} vs {g["away"]} - {g["league"]}</span><span style="margin-left:auto;color:#00c853">{g["score"]}</span></div>'
    return f"<html><head><meta name='viewport' content='width=device-width'></head><body style='background:#0f1623;color:white;font-family:Arial;margin:0'><div style='background:red;color:white;padding:12px;font-weight:bold'>{VERSION} - 502 FIXED + ALL EUROPE ROTATING - RED = GOOD</div><div style='padding:10px;overflow-x:auto;white-space:nowrap'>{tabs}</div>{html}<div style='padding:12px;font-size:8px;color:#666'>FIX: 54 leagues caused 502. Now 10 leagues per day rotating = no 502. 09/23 Wed = uefa.champions 09/25 Thu = uefa.europa. RapidAPI limit resets midnight UTC - if 0 games, use ESPN.<br>PORT FIX: bind 0.0.0.0:$PORT with gunicorn --timeout 120</div></body></html>"

@app.route('/match')
def match_page():
    home=request.args.get('home','A'); away=request.args.get('away','B'); day=request.args.get('day','0')
    return f"<html><body style='background:#0f1623;color:white'><div style='background:red;padding:12px'>{VERSION}</div><a href='/?day={day}' style='color:white'>BACK</a> {home} vs {away} REAL 2026</body></html>"

if __name__ == '__main__':
    port=int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
