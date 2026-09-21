from flask import Flask, request
import requests, os, time
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
app = Flask(__name__)
HEADERS={"User-Agent":"Mozilla/5.0","Accept":"application/json"}

FLAGS={"England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Germany":"🇩🇪","Spain":"🇪🇸","Italy":"🇮🇹","France":"🇫🇷","Netherlands":"🇳🇱","USA":"🇺🇸","South Africa":"🇿🇦","Turkey":"🇹🇷","Sweden":"🇸🇪","Switzerland":"🇨🇭","Saudi Arabia":"🇸🇦","China":"🇨🇳","Azerbaijan":"🇦🇿","Denmark":"🇩🇰","Croatia":"🇭🇷","Greece":"🇬🇷","Ireland":"🇮🇪","Norway":"🇳🇴","Portugal":"🇵🇹","Ukraine":"🇺🇦","Spain":"🇪🇸","Euro Cups":"🏆","FIFA Competition":"🌍"}

COUNTRIES=["Croatia","Denmark","England","Germany","Spain","Italy","France","Netherlands","USA","South Africa","Sweden","Turkey","Switzerland","Saudi Arabia","China","Azerbaijan","Greece","Ireland","Norway","Portugal","Ukraine","Euro Cups","FIFA Competition"]

CACHE={"t":0,"data":{}, "date":""}

def get_sofascore(date_str):
    if CACHE["date"]==date_str and time.time()-CACHE["t"]<50 and CACHE["data"]:
        return CACHE["data"]
    out={c: {} for c in COUNTRIES} # country -> league -> games
    try:
        url=f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
        r=requests.get(url, headers=HEADERS, timeout=7)
        if r.status_code==200:
            for ev in r.json().get('events',[])[:400]:
                home=ev.get('homeTeam',{}).get('name','')
                away=ev.get('awayTeam',{}).get('name','')
                if not home: continue
                cat=ev.get('tournament',{}).get('category',{}).get('name','') or ''
                tour=ev.get('tournament',{}).get('name','') or ''
                ts=ev.get('startTimestamp',0)
                dt=datetime.fromtimestamp(ts)+timedelta(hours=2)
                kickoff=dt.strftime("%H:%M")
                hs=ev.get('homeScore',{}).get('current','')
                aws=ev.get('awayScore',{}).get('current','')
                stype=ev.get('status',{}).get('type','')
                score=f"{hs}-{aws} FT" if stype=='finished' else f"LIVE {hs}-{aws}" if stype=='inprogress' else f"{kickoff}"

                cat_l=cat.lower(); tour_l=tour.lower()
                cname=None
                if 'croatia' in cat_l: cname="Croatia"
                elif 'denmark' in cat_l: cname="Denmark"
                elif 'england' in cat_l: cname="England"
                elif 'germany' in cat_l: cname="Germany"
                elif 'spain' in cat_l: cname="Spain"
                elif 'italy' in cat_l: cname="Italy"
                elif 'france' in cat_l: cname="France"
                elif 'netherlands' in cat_l: cname="Netherlands"
                elif 'usa' in cat_l or 'united states' in cat_l: cname="USA"
                elif 'sweden' in cat_l: cname="Sweden"
                elif 'turkey' in cat_l: cname="Turkey"
                elif 'switzerland' in cat_l: cname="Switzerland"
                elif 'saudi' in cat_l: cname="Saudi Arabia"
                elif 'china' in cat_l: cname="China"
                elif 'azerbaijan' in cat_l: cname="Azerbaijan"
                elif 'greece' in cat_l: cname="Greece"
                elif 'ireland' in cat_l: cname="Ireland"
                elif 'norway' in cat_l: cname="Norway"
                elif 'portugal' in cat_l: cname="Portugal"
                elif 'ukraine' in cat_l: cname="Ukraine"
                elif 'south africa' in cat_l: cname="South Africa"
                elif 'uefa' in cat_l or 'champions' in tour_l or 'europa' in tour_l: cname="Euro Cups"
                elif 'world' in tour_l or 'fifa' in tour_l: cname="FIFA Competition"
                if not cname or cname not in out: continue

                # Determine pro/amateur/cup for sub label like SofaScore
                tier="Pro"
                if 'future cup' in tour_l or 'amateur' in tour_l: tier="Amateur"
                elif 'cup' in tour_l: tier="Cup"
                elif '2' in tour or '1. division' in tour_l or 'betinia' in tour_l: tier="Pro 2"

                league_key=f"{tour} ({tier})"
                if league_key not in out[cname]:
                    out[cname][league_key]=[]
                out[cname][league_key].append({"home":home,"away":away,"kickoff":kickoff,"score":score,"tier":tier,"league":tour,"full":dt.strftime("%d/%m %H:%M CAT"),"id":str(ev.get('id',''))})
    except Exception as e:
        print(e)
    CACHE["data"]=out; CACHE["t"]=time.time(); CACHE["date"]=date_str
    return out

@app.route('/')
def home():
    day=request.args.get('day','0')
    date_str=(datetime(2026,9,21)+timedelta(days=int(day))).strftime("%Y-%m-%d")
    data=get_sofascore(date_str)
    total=sum(sum(len(v) for v in leagues.values()) for leagues in data.values())
    tabs="".join([f'<a href="/?day={i}" style="background:{"#00c853" if str(i)==day else "#242F44"};color:{"black" if str(i)==day else "white"};padding:7px 12px;border-radius:20px;text-decoration:none;margin-right:5px;font-size:11px">{i} 09/{21+int(i)}</a>' for i in range(7)])

    html=f"""
    <div style="background:#00c853;color:black;padding:12px;font-weight:bold;font-size:14px">ABED PREDICT WORLD - {date_str} - {total} games - SOFASCORE DROPDOWN THEME</div>
    <div style="background:#0f1623;padding:10px;display:flex;gap:10px;overflow-x:auto;white-space:nowrap;position:sticky;top:0;z-index:20">
        <div style="background:#1e2a3a;padding:6px 12px;border-radius:20px;font-size:11px;color:#00c853;border:1px solid #00c853">⚽ Football</div>
        <div style="background:#242F44;padding:6px 12px;border-radius:20px;font-size:11px;color:#888">🎾 Tennis</div>
        <div style="background:#242F44;padding:6px 12px;border-radius:20px;font-size:11px;color:#888">🏀 Basketball</div>
    </div>
    <div style="background:#1a2332;padding:10px;display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;gap:8px"><span style="background:#242F44;padding:5px 10px;border-radius:15px;font-size:11px">② Filter</span><span style="background:#3a0a0a;color:#ff5252;padding:5px 10px;border-radius:15px;font-size:11px">Live ○</span></div>
        <div style="display:flex;gap:10px;align-items:center"><a href="/?day={max(0,int(day)-1)}" style="color:#00c853;text-decoration:none">‹</a><span style="color:#7aa5ff;font-size:12px">Today</span><a href="/?day={min(6,int(day)+1)}" style="color:#00c853;text-decoration:none">›</a></div>
    </div>
    <div style="background:#0f1623;padding:8px;display:flex;gap:10px"><span style="background:white;color:black;padding:6px 18px;border-radius:20px;font-size:12px;font-weight:bold">MATCHES</span><span style="color:#888;padding:6px 18px;font-size:12px">LEAGUES</span></div>
    <div style="padding:10px;overflow-x:auto;white-space:nowrap;background:#0f1623">{tabs}</div>
    """

    for country in COUNTRIES:
        leagues=data.get(country,{})
        count=sum(len(g) for g in leagues.values())
        if count==0: continue
        flag=FLAGS.get(country,"⚽")
        html+=f'''
        <div onclick="toggleCountry('{country}')" style="background:#1e2a3a;margin:6px 8px;border-radius:12px;padding:12px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;border:1px solid #242F44">
            <div style="display:flex;gap:10px;align-items:center"><span style="font-size:18px">{flag}</span><div><div style="color:white;font-size:13px;font-weight:bold">{country}</div><div style="color:#888;font-size:10px">{list(leagues.keys())[0].split('(')[0] if leagues else ''} { "Amateur" if any("Amateur" in k for k in leagues) else ""}</div></div></div>
            <div style="display:flex;gap:8px;align-items:center"><span style="background:#242F44;color:#888;padding:4px 8px;border-radius:12px;font-size:11px">{count}</span><span id="arrow-{country}" style="color:#888">▼</span></div>
        </div>
        <div id="country-{country}" style="display:none;margin:0 8px">
        '''
        for league_key, games in leagues.items():
            # League header like SofaScore Betinia Liga Denmark
            html+=f'''
            <div onclick="event.stopPropagation(); toggleLeague('{country}-{league_key}')" style="background:#242F44;margin:4px 0;border-radius:10px;padding:10px;display:flex;justify-content:space-between;align-items:center;cursor:pointer">
                <div style="display:flex;gap:8px;align-items:center"><span style="background:#1a2332;padding:4px 6px;border-radius:6px;font-size:9px;color:#00c853">BETINIA LIGA</span><div><div style="color:white;font-size:12px">{league_key.split('(')[0]}</div><div style="color:#888;font-size:10px">{country} {league_key.split('(')[-1].replace(')','')}</div></div></div>
                <div style="display:flex;gap:8px"><span style="color:#444">☆</span><span id="arrow-{country}-{league_key}" style="color:#888;font-size:10px">▲</span></div>
            </div>
            <div id="league-{country}-{league_key}" style="display:block">
            '''
            for g in games[:10]:
                link=f"/match?home={quote(g['home'])}&away={quote(g['away'])}&league={quote(g['league'])}&score={quote(g['score'])}&country={quote(country)}&date={date_str}&kickoff={quote(g['full'])}"
                html+=f'<a href="{link}" style="text-decoration:none"><div style="background:#0f1623;border-bottom:1px solid #1a2332;padding:10px 12px;display:flex;justify-content:space-between;align-items:center"><div style="display:flex;gap:12px;align-items:center"><span style="color:#888;font-size:12px;width:35px">{g["kickoff"]}<br><span style="color:#444">-</span></span><div><div style="color:white;font-size:12px;display:flex;gap:6px;align-items:center"><span>🔵</span> {g["home"]}</div><div style="color:white;font-size:12px;display:flex;gap:6px;align-items:center"><span>🔴</span> {g["away"]}</div></div></div><div style="color:#888">🔔</div></div></a>'
            html+='</div>'
        html+='</div>'

    html+='<div style="background:#1e2a3a;margin-top:20px;padding:12px;font-size:10px;color:#666">Dropdown menu like SofaScore • Different theme ABED green/black • Kickoff time CAT • Live feed 25s reload</div>'

    js='''
    <script>
    function toggleCountry(n){
        var e=document.getElementById("country-"+n);
        var a=document.getElementById("arrow-"+n);
        if(e.style.display=="none"){e.style.display="block";a.innerText="▲";} else {e.style.display="none";a.innerText="▼";}
    }
    function toggleLeague(id){
        var e=document.getElementById("league-"+id);
        var a=document.getElementById("arrow-"+id);
        if(e.style.display=="none"){e.style.display="block";a.innerText="▲";} else {e.style.display="none";a.innerText="▼";}
    }
    setTimeout(function(){ if(document.body.innerHTML.includes("LIVE")) location.reload(); }, 25000);
    </script>
    '''
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'><title>ABED PREDICT WORLD</title></head><body style='background:#0f1623;color:white;font-family:Arial;margin:0'>{html}{js}</body></html>"

@app.route('/match')
def match_page():
    h=unquote(request.args.get('home','')); a=unquote(request.args.get('away','')); l=unquote(request.args.get('league','')); s=unquote(request.args.get('score','')); k=unquote(request.args.get('kickoff','')); c=unquote(request.args.get('country',''))
    return f"<html><body style='background:#0f1623;color:white;font-family:Arial;margin:0'><div style='background:#00c853;color:black;padding:12px'><a href='/' style='color:black;text-decoration:none'>← BACK</a> {h} vs {a}</div><div style='padding:12px'><div style='background:#1e2a3a;padding:15px;border-radius:12px;border-left:4px solid #00c853'><b>{h} vs {a}</b><br>{l} - {c}<br>🕐 {k} CAT<br>{s}<br><br>Dropdown like SofaScore, theme ABED green/black<br>Prediction, H2H, Lineup, Stats clickable here</div></div></body></html>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT",10000)))
