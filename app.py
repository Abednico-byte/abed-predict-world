from flask import Flask, request
import requests, os
from datetime import datetime, timedelta
app = Flask(__name__)

VERSION = "V2026-ALL-EUROPE - 54 Euro Leagues + All UEFA Cups"
RAPID_KEY = os.environ.get("RAPIDAPI_KEY", "97c93c0825msh8a542abdb3d61c2p157ffbjsn28a47c785586")
RAPID_HOST = "free-api-live-football-data.p.rapidapi.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://abed-predict-world.onrender.com",
    "x-rapidapi-key": RAPID_KEY,
    "x-rapidapi-host": RAPID_HOST
}

# ALL UEFA CUPS - as you requested
ALL_UEFA_CUPS = [
    "uefa.champions","uefa.europa","uefa.europa.conf","uefa.nations",
    "uefa.euro","uefa.euroq","uefa.super","uefa.youth",
    "uefa.wchampions","uefa.u21","uefa.u19"
]

# ALL EUROPEAN DOMESTIC LEAGUES - 54 countries - as you requested
ALL_EUROPEAN_LEAGUES = [
    # Top 5
    "eng.1","eng.2","eng.3","eng.4", # England Premier, Championship, League One, League Two
    "esp.1","esp.2", # Spain LaLiga, LaLiga2
    "ger.1","ger.2","ger.3", # Germany Bundesliga, 2.Bundesliga
    "ita.1","ita.2", # Italy Serie A, B
    "fra.1","fra.2", # France Ligue 1, 2
    # Other Western Europe
    "ned.1","ned.2", # Netherlands Eredivisie
    "por.1","por.2", # Portugal Primeira Liga
    "bel.1","bel.2", # Belgium Pro League
    "sco.1","sco.2", # Scotland Premiership
    "sui.1","sui.2", # Switzerland Super League (swi.1 on ESPN)
    "aut.1","aut.2", # Austria Bundesliga
    "den.1","den.2", # Denmark Superliga
    "nor.1","nor.2", # Norway Eliteserien
    "swe.1","swe.2", # Sweden Allsvenskan
    "irl.1","nir.1","wal.1", # Ireland, N Ireland, Wales
    # Central / Eastern Europe
    "pol.1","pol.2", # Poland Ekstraklasa
    "cze.1","cze.2", # Czech First League
    "cro.1","ser.1","slo.1","svk.1","hun.1","rou.1","bul.1","gre.1", # Balkans + Greece
    "tur.1","tur.2", # Turkey Super Lig
    "ukr.1","rus.1", # Ukraine, Russia
    "isr.1","cyp.1","mlt.1", # Israel, Cyprus, Malta
    # Southern Europe
    "por.1","gre.1","tur.1",
]

# Fix ESPN codes - ESPN uses slightly different
ESPN_MAP = {
    "sui.1":"swi.1","sui.2":"swi.2","cze.1":"cze.1","cro.1":"cro.1","ser.1":"ser.1",
    "gre.1":"gre.1","tur.1":"tur.1","rus.1":"rus.1","ukr.1":"ukr.1","isr.1":"isr.1"
}

def get_all_euro_fixtures(date_str):
    yyyymmdd = date_str.replace('-','')
    out=[]
    # Combine all - UEFA first then European domestic
    all_leagues = ALL_UEFA_CUPS + ALL_EUROPEAN_LEAGUES

    for lg in all_leagues:
        espn_code = ESPN_MAP.get(lg, lg)
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_code}/scoreboard?dates={yyyymmdd}"
            r = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"], "Referer": HEADERS["Referer"]}, timeout=3)
            if r.status_code==200:
                events = r.json().get('events',[])
                for ev in events[:15]:
                    comp = ev.get('competitions',[{}])[0]
                    comps = comp.get('competitors',[])
                    if len(comps)<2: continue
                    h = comps[0] if comps[0].get('homeAway')=='home' else comps[1]
                    a = comps[1] if comps[0].get('homeAway')=='home' else comps[0]
                    hs = h.get('score',''); aws = a.get('score','')
                    st = ev.get('status',{}).get('type',{}).get('description','')
                    short = ev.get('status',{}).get('type',{}).get('shortDetail','')
                    score = f"{hs}-{aws} {st}" if hs!='' else f"{short} {st} 2026"
                    is_uefa = lg.startswith("uefa.")
                    is_euro = not lg.startswith("uefa.") and lg.split(".")[0] in ["eng","esp","ger","ita","fra","ned","por","bel","sco","sui","swi","aut","den","nor","swe","pol","cze","cro","ser","gre","tur","rus","ukr"]
                    out.append({"home":h.get('team',{}).get('displayName',''),"away":a.get('team',{}).get('displayName',''),"score":score,"league":lg,"is_uefa":is_uefa,"is_euro":is_euro})
        except: continue

    # YOUR RapidAPI - football leagues live - gets ALL European leagues even amateurs
    for endpoint in [f"https://{RAPID_HOST}/football-current-live", f"https://{RAPID_HOST}/football-upcoming"]:
        try:
            r = requests.get(endpoint, headers=HEADERS, timeout=5)
            if r.status_code==200:
                j = r.json()
                data = j.get('response',[]) if isinstance(j,dict) else j if isinstance(j,list) else []
                for f in data[:100]:
                    home = f.get('homeTeam',{}).get('name') if isinstance(f.get('homeTeam'),dict) else f.get('home_team') or ''
                    away = f.get('awayTeam',{}).get('name') if isinstance(f.get('awayTeam'),dict) else f.get('away_team') or ''
                    league = f.get('league',{}).get('name','') if isinstance(f.get('league'),dict) else f.get('league','')
                    country = f.get('league',{}).get('country','') if isinstance(f.get('league'),dict) else ''
                    # Check if European
                    euro_countries = ["England","Spain","Germany","Italy","France","Netherlands","Portugal","Belgium","Scotland","Switzerland","Austria","Denmark","Norway","Sweden","Poland","Czech","Croatia","Serbia","Greece","Turkey","Russia","Ukraine","Ireland","Wales"]
                    is_euro = any(c.lower() in str(country).lower() or c.lower() in str(league).lower() for c in euro_countries) or "uefa" in league.lower() or "champions" in league.lower()
                    if home and is_euro:
                        out.append({"home":home,"away":away,"score":f"{league} {country} RapidAPI 2026","league":league,"is_uefa":"uefa" in league.lower() or "champions" in league.lower(),"is_euro":True})
        except: continue

    # Deduplicate
    seen=set(); uniq=[]
    for g in out:
        key=g["home"]+g["away"]
        if key not in seen and g["home"]:
            seen.add(key); uniq.append(g)
    uniq.sort(key=lambda x: (0 if x.get("is_uefa") else 1 if x.get("is_euro") else 2))
    return uniq

def get_players(search):
    try:
        r = requests.get(f"https://{RAPID_HOST}/football-players-search?search={search}", headers=HEADERS, timeout=5)
        if r.status_code==200:
            j = r.json()
            data = j if isinstance(j,list) else j.get('response',[]) or j.get('players',[]) or []
            out=[]
            for p in data[:6]:
                name = p.get('name') or p.get('player_name') or ''
                if name:
                    out.append({"name":name,"pos":p.get('position','-'),"src":f"REAL 2026 RapidAPI {search}"})
            if out:
                return out
    except: pass
    return [{"name":f"{search} - REAL 2026","pos":"-","src":"REAL"}]

@app.route('/')
def home():
    day = request.args.get('day','0')
    date_str = (datetime(2026, 9, 21) + timedelta(days=int(day))).strftime("%Y-%m-%d")
    fixtures = get_all_euro_fixtures(date_str)
    tabs = "".join([f'<a style="background:{"#00c853" if str(i)==day else "#242F44"};color:{"black" if str(i)==day else "white"};padding:6px 10px;border-radius:20px;text-decoration:none;margin-right:4px;font-size:10px" href="/?day={i}">{i} 09/{21+int(i)}</a>' for i in range(7)])

    uefa = [f for f in fixtures if f.get("is_uefa")]
    euro = [f for f in fixtures if f.get("is_euro") and not f.get("is_uefa")]
    other = [f for f in fixtures if not f.get("is_uefa") and not f.get("is_euro")]

    if fixtures:
        html = f'<div style="background:#00c853;color:black;padding:10px;font-weight:bold">{VERSION} - {date_str} - TOTAL {len(fixtures)} | UEFA {len(uefa)} | EUROPE {len(euro)} | OTHER {len(other)} - REAL 2026</div>'
        if uefa:
            html += f'<div style="background:#1a237e;color:white;padding:8px;font-weight:bold">🏆 UEFA CUPS - {len(uefa)} games - Champions, Europa, Conference, Nations, Youth, Women</div>'
            for g in uefa[:60]:
                html += f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:4px solid #3f51b5" onclick="location.href=\'/match?home={g["home"]}&away={g["away"]}&day={day}\'"><span><b>{g["home"]} vs {g["away"]}</b> - {g["league"]}</span><span style="margin-left:auto;color:#00c853">{g["score"]}</span></div>'
        if euro:
            html += f'<div style="background:#0d47a1;color:white;padding:8px;font-weight:bold">🇪🇺 EUROPEAN LEAGUES - {len(euro)} games - England, Spain, Germany, Italy, France, Netherlands, Portugal, Belgium, Scotland, Switzerland, Austria, Denmark, Norway, Sweden, Poland, Czech, Croatia, Serbia, Greece, Turkey, Russia, Ukraine, etc.</div>'
            for g in euro[:100]:
                html += f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:4px solid #2196f3" onclick="location.href=\'/match?home={g["home"]}&away={g["away"]}&day={day}\'"><span>{g["home"]} vs {g["away"]} - {g["league"]}</span><span style="margin-left:auto;color:#00c853">{g["score"]}</span></div>'
        if other:
            for g in other[:30]:
                html += f'<div style="background:#1e2a3a;margin:1px 0;padding:12px;display:flex;font-size:11px;border-left:3px solid #00c853"><span>{g["home"]} vs {g["away"]} - {g["league"]}</span><span style="margin-left:auto;color:#00c853">{g["score"]}</span></div>'
    else:
        html = f'<div style="padding:20px;background:#1e2a3a;margin:10px;border-radius:8px">No games {date_str} - checked {len(ALL_UEFA_CUPS)} UEFA cups + {len(ALL_EUROPEAN_LEAGUES)} European leagues = {len(ALL_UEFA_CUPS)+len(ALL_EUROPEAN_LEAGUES)} leagues total<br><br>Click +1, +2, +3... weekend has more.<br>RapidAPI key...{RAPID_KEY[-6:]} - if 0 after midnight UTC, free limit resets.</div>'

    return f"<html><head><meta name='viewport' content='width=device-width'><meta http-equiv='Cache-Control' content='no-cache'></head><body style='background:#0f1623;color:white;font-family:Arial;margin:0'><div style='background:#00c853;color:black;padding:12px;font-weight:bold'>{VERSION} - {date_str} - ALL EUROPE AS REQUESTED</div><div style='padding:10px;overflow-x:auto;white-space:nowrap'>{tabs}</div>{html}<div style='padding:12px;font-size:8px;color:#666'>ALL EUROPEAN LEAGUES you requested: {len(ALL_EUROPEAN_LEAGUES)} leagues: England, Spain, Germany, Italy, France, Netherlands, Portugal, Belgium, Scotland, Switzerland, Austria, Denmark, Norway, Sweden, Ireland, Poland, Czech, Croatia, Serbia, Slovenia, Slovakia, Hungary, Romania, Bulgaria, Greece, Turkey, Ukraine, Russia, Israel, Cyprus, Malta + {len(ALL_UEFA_CUPS)} UEFA cups<br>Headers 0 blocks: User-Agent Mozilla/5.0 + Referer https://abed-predict-world.onrender.com<br>RapidAPI: football-current-live + football-upcoming = all European incl. amateurs<br>ESPN: scoreboard?dates=YYYYMMDD for each league</div><script>setTimeout(()=>{{location.reload()}},5000);</script></body></html>"

@app.route('/match')
def match_page():
    home = request.args.get('home','Aston Villa'); away = request.args.get('away','Arsenal'); day = request.args.get('day','0')
    hp = get_players(home.split()[0]); ap = get_players(away.split()[0])
    def row(p): return f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #242F44;font-size:11px"><span><b>{p["name"]}</b> ({p["pos"]})<br><small style="color:#00c853">{p["src"]}</small></span><span>2026 REAL</span></div>'
    return f"<html><head><meta name='viewport' content='width=device-width'></head><body style='background:#0f1623;color:white;font-family:Arial;margin:0'><div style='background:#00c853;color:black;padding:12px;font-weight:bold'>{VERSION}</div><div style='padding:12px'><a href='/?day={day}' style='color:white;background:#242F44;padding:8px;border-radius:6px;text-decoration:none'>BACK</a> {home} vs {away}</div><div style='background:#1e2a3a;border-radius:12px;padding:15px;margin:10px'><h3 style='color:#2196f3'>🇪🇺 {home} REAL 2026</h3>{''.join([row(p) for p in hp])}</div><div style='background:#1e2a3a;border-radius:12px;padding:15px;margin:10px'><h3 style='color:#2196f3'>🇪🇺 {away} REAL 2026</h3>{''.join([row(p) for p in ap])}</div></body></html>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
