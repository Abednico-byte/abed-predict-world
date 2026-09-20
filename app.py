from flask import Flask, request
import requests, os
from datetime import datetime, timedelta
app = Flask(__name__)

RAPID_KEY = os.environ.get("RAPIDAPI_KEY", "97c93c0825msh8a542abdb3d61c2p157ffbjsn28a47c785586")
RAPID_HOST = "free-api-live-football-data.p.rapidapi.com"
HEADERS = {"User-Agent":"Mozilla/5.0","Referer":"https://abed-predict-world.onrender.com","x-rapidapi-key":RAPID_KEY,"x-rapidapi-host":RAPID_HOST}

# ALL leagues you originally had
PREMATCH_LEAGUES = [
    # Europe Top - prematch
    "eng.1","eng.2","esp.1","ger.1","ita.1","fra.1","ned.1","por.1","bel.1","sco.1","tur.1","sui.1",
    # UEFA - prematch
    "uefa.champions","uefa.europa","uefa.europa.conf","uefa.nations",
    # AMERICAN - THIS WAS MISSING - as you asked
    "usa.1","usa.2","mex.1","bra.1","arg.1","usa.nwsl","concacaf.champions","conmebol.libertadores",
    # Other world for prematch
    "aus.1","jpn.1","chn.1"
]

def get_prematch_american(date_str):
    yyyymmdd = date_str.replace('-','')
    out=[]
    for lg in PREMATCH_LEAGUES:
        try:
            espn_code = "swi.1" if lg=="sui.1" else lg
            # WITH dates = PREMATCH + LIVE + FT - THIS IS PREMATCH YOU ASKED
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={yyyymmdd}"
            r = requests.get(url, headers={"User-Agent":HEADERS["User-Agent"],"Referer":HEADERS["Referer"]}, timeout=2)
            if r.status_code==200:
                for ev in r.json().get('events',[])[:15]:
                    comp=ev.get('competitions',[{}])[0]; comps=comp.get('competitors',[])
                    if len(comps)<2: continue
                    h=comps[0] if comps[0].get('homeAway')=='home' else comps[1]
                    a=comps[1] if comps[0].get('homeAway')=='home' else comps[0]
                    hs=h.get('score',''); aws=a.get('score','')
                    st=ev.get('status',{}).get('type',{}).get('description','')
                    short=ev.get('status',{}).get('type',{}).get('shortDetail','')
                    # PREMATCH shows as "Scheduled" or time like "8:00 PM"
                    is_prematch = st.lower() in ["scheduled","pre","preview"] or "pm" in short.lower() or "am" in short.lower()
                    score=f"{hs}-{aws} {st}" if hs!='' else f"{short} - PREMATCH" if is_prematch else f"{short} {st}"
                    is_american = lg.startswith("usa.") or lg.startswith("mex.") or lg.startswith("bra.") or lg.startswith("arg.") or "concacaf" in lg or "libertadores" in lg
                    is_uefa = lg.startswith("uefa.")
                    out.append({"home":h.get('team',{}).get('displayName',''),"away":a.get('team',{}).get('displayName',''),"score":score,"league":lg,"is_american":is_american,"is_uefa":is_uefa,"is_prematch":is_prematch})
        except: continue
    return out

@app.route('/')
def home():
    day=request.args.get('day','0')
    date_str=(datetime(2026,9,21)+timedelta(days=int(day))).strftime("%Y-%m-%d")
    fixtures=get_prematch_american(date_str)
    tabs="".join([f'<a style="background:{"#00c853" if str(i)==day else "#242F44"};color:{"black" if str(i)==day else "white"};padding:6px 10px;border-radius:20px;text-decoration:none;margin-right:4px;font-size:10px" href="/?day={i}">{i} 09/{21+int(i)}</a>' for i in range(7)])

    prematch=[f for f in fixtures if f.get("is_prematch")]
    american=[f for f in fixtures if f.get("is_american")]
    uefa=[f for f in fixtures if f.get("is_uefa")]
    europe=[f for f in fixtures if not f.get("is_american") and not f.get("is_uefa")]

    html=f'<div style="background:#00c853;color:black;padding:8px;font-weight:bold">ABED PREDICT WORLD - {date_str} - PREMATCH {len(prematch)} | AMERICAN {len(american)} | UEFA {len(uefa)} | EUROPE {len(europe)} | TOTAL {len(fixtures)} - 7 days - 5-sec</div>'

    if american:
        html+=f'<div style="background:#b71c1c;color:white;padding:8px;font-weight:bold">🇺🇸 AMERICAN - {len(american)} games - MLS, Liga MX, Brazil, Argentina, NWSL, Libertadores - PREMATCH</div>'
        for g in american[:60]:
            html+=f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:4px solid #ff5252"><span><b>{g["home"]} vs {g["away"]}</b> - {g["league"]}</span><span style="margin-left:auto;color:#ff5252">{g["score"]}</span></div>'
    if uefa:
        html+=f'<div style="background:#1a237e;color:white;padding:8px;font-weight:bold">🏆 UEFA - {len(uefa)} games - Champions Europa Conference Nations - PREMATCH</div>'
        for g in uefa[:40]:
            html+=f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:4px solid #3f51b5"><span><b>{g["home"]} vs {g["away"]}</b></span><span style="margin-left:auto;color:#00c853">{g["score"]}</span></div>'
    if europe:
        html+=f'<div style="background:#0d47a1;color:white;padding:8px;font-weight:bold">🇪🇺 EUROPE - {len(europe)} games - England Spain Germany Italy France Netherlands Portugal etc. - PREMATCH</div>'
        for g in europe[:80]:
            html+=f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:4px solid #2196f3"><span>{g["home"]} vs {g["away"]} - {g["league"]}</span><span style="margin-left:auto;color:#00c853">{g["score"]}</span></div>'

    if not fixtures:
        html=f'<div style="background:#00c853;color:black;padding:8px">ABED PREDICT WORLD - {date_str} - 0 games - ESPN off-season for this date</div><div style="padding:20px;background:#1e2a3a">No games {date_str}. Try day 5 09/26 Saturday = 50+ prematch. Prematch uses?dates={date_str.replace("-","")} = scheduled time like 8:00 PM PREMATCH.<br>American games: usa.1 MLS, mex.1 Liga MX, bra.1, arg.1 - only show during American evening (after 2AM Gaborone time).</div>'

    return f"<html><head><meta name='viewport' content='width=device-width'></head><body style='background:#0f1623;color:white;font-family:Arial;margin:0'><div style='padding:10px;overflow-x:auto;white-space:nowrap'>{tabs}</div>{html}<div style='padding:10px;font-size:8px;color:#666'>PREMATCH RESTORED: Using?dates=YYYYMMDD returns Scheduled/Preview with time like 8:00 PM PREMATCH. AMERICAN RESTORED: usa.1 MLS, mex.1 Liga MX, bra.1 Brasileirão, arg.1, concacaf.champions, conmebol.libertadores. Total {len(PREMATCH_LEAGUES)} leagues with prematch.</div><script>setTimeout(()=>{{location.reload()}},5000);</script></body></html>"

if __name__ == '__main__':
    port=int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
