import os, hashlib, requests
from flask import Flask, jsonify, request
from datetime import datetime, timezone, timedelta
import urllib.parse

app = Flask(__name__)
BOTSWANA_TZ = timezone(timedelta(hours=2))
REQUEST_TIMEOUT = 10

def hash_int(s): return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:6],16)

def last5(team):
    h=hash_int(team); values=[]; seed=h
    for i in range(5):
        gf=((seed >> (i*3)) & 7) % 4; ga=((seed >> (i*2+1)) & 7) % 3
        values.append((gf,ga))
    wins=sum(1 for gf,ga in values if gf>ga); draws=sum(1 for gf,ga in values if gf==ga)
    avg_gf=sum(gf for gf,ga in values)/5.0; avg_ga=sum(ga for gf,ga in values)/5.0
    btts=sum(1 for gf,ga in values if gf>0 and ga>0)/5.0
    return {"wins":wins,"draws":draws,"avg_gf":avg_gf,"avg_ga":avg_ga,"btts":btts,"g":values}

def calc(home,away):
    hs=last5(home); aw=last5(away)
    h_str=hs["avg_gf"]*0.60+max(0,5-hs["avg_ga"])*0.20+hs["wins"]*0.20+0.40
    a_str=aw["avg_gf"]*0.60+max(0,5-aw["avg_ga"])*0.20+aw["wins"]*0.20
    total=max(h_str+a_str,0.01)
    hp=h_str/total*78; ap=a_str/total*78; dp=100-hp-ap
    if dp<12: e=12-dp; hp-=e/2; ap-=e/2; dp=12
    if dp>35: e=dp-35; hp+=e/2; ap+=e/2; dp=35
    hp=round(max(1,hp),1); dp=round(max(1,dp),1); ap=round(max(1,100-hp-dp),1)
    eg=max(0.2,min(5.0,(hs["avg_gf"]+aw["avg_gf"])*0.65+(hs["avg_ga"]+aw["avg_ga"])*0.35+0.55))
    def over(l): return round(min(95,max(5,50+(eg-l)*17)),1)
    o05=over(0.5); o15=over(1.5); o25=over(2.5); o35=over(3.5); o45=over(4.5)
    btts_yes=round(min(88,max(22,(hs["btts"]+aw["btts"])/2*100*0.85+10)),1)
    return {"hp":hp,"dp":dp,"ap":ap,"1x":round(hp+dp,1),"12":round(hp+ap,1),"x2":round(dp+ap,1),"o05":o05,"u05":round(100-o05,1),"o15":o15,"u15":round(100-o15,1),"o25":o25,"u25":round(100-o25,1),"o35":o35,"u35":round(100-o35,1),"o45":o45,"u45":round(100-o45,1),"bttsY":btts_yes,"bttsN":round(100-btts_yes,1),"hs":hs,"aw":aw,"expected_goals":round(eg,2),"model_note":"Deterministic fallback model; connect real L5/H2H data for production betting analysis."}

def classify_country(l):
    low=(l or "").lower()
    if any(x in low for x in ["england","premier league","championship","fa cup"]): return "England","🏴󠁧󐁢󐁥󐁮󐁧󐁿"
    if any(x in low for x in ["knvb","dutch","eredivisie","netherlands"]): return "Netherlands","🇳🇱"
    if any(x in low for x in ["spain","laliga"]): return "Spain","🇪🇸"
    if any(x in low for x in ["bundes","germany"]): return "Germany","🇩🇪"
    if any(x in low for x in ["serie","italy"]): return "Italy","🇮🇹"
    if any(x in low for x in ["ligue","france"]): return "France","🇫🇷"
    if any(x in low for x in ["uefa","champions"]): return "Europe","🇪🇺"
    if "women" in low: return "World Women","🌍"
    return "World","🌍"

def fetch_espn():
    games=[]
    now=datetime.now(BOTSWANA_TZ)
    dates=[(now+timedelta(days=d)).strftime("%Y%m%d") for d in [0,-1,1,2]]
    LEAGUES=["eng.1","eng.2","eng.fa","esp.1","ger.1","ita.1","fra.1","ned.1","ned.cup","por.1","bel.1","tur.1","sco.1","den.1","swe.1","rsa.1","usa.1","uefa.champions","uefa.europa","uefa.wchampions","uefa.europa.conf"]
    
    headers={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept":"application/json, text/plain, */*",
        "Accept-Language":"en-US,en;q=0.9",
        "Referer":"https://www.espn.com/soccer/",
        "Origin":"https://www.espn.com",
    }

    def get_json(url):
        # 1. Direct – now uses the working site.web.api host
        try:
            r=requests.get(url,headers=headers,timeout=REQUEST_TIMEOUT)
            if r.status_code==200:
                return r.json()
        except: pass
        # 2. Proxy fallback
        try:
            proxy_url="https://api.allorigins.win/raw?url="+urllib.parse.quote(url, safe='')
            r=requests.get(proxy_url,headers=headers,timeout=12)
            if r.status_code==200:
                return r.json()
        except: pass
        return None

    for date_str in dates:
        if len(games)>40: break

        # ALL (most reliable single call)
        data=get_json(f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}&limit=400")
        if data:
            for ev in data.get("events",[]):
                comp=(ev.get("competitions") or [{}])[0]
                cs=comp.get("competitors") or []
                if len(cs)<2: continue
                home=next((x for x in cs if x.get("homeAway")=="home"),cs[0])
                away=next((x for x in cs if x.get("homeAway")=="away"),cs[1])
                lname=(data.get("leagues",[{}])[0].get("name") if data.get("leagues") else None) or ev.get("shortName") or "Football"
                country,flag=classify_country(lname)
                st=(comp.get("status",{}).get("type",{}) or {})
                games.append({
                    "league":lname,
                    "leagueName":lname,
                    "country":country,
                    "flag":flag,
                    "home":(home.get("team",{}).get("displayName") or "Home")[:40],
                    "away":(away.get("team",{}).get("displayName") or "Away")[:40],
                    "score":st.get("shortDetail") or "TBD",
                    "live":st.get("state")=="in"
                })

        # League-specific (extra coverage)
        if len(games)<15:
            for code in LEAGUES:
                if len(games)>40: break
                data=get_json(f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_str}")
                if not data: continue
                for ev in data.get("events",[])[:4]:
                    comp=(ev.get("competitions") or [{}])[0]
                    cs=comp.get("competitors") or []
                    if len(cs)<2: continue
                    home=next((x for x in cs if x.get("homeAway")=="home"),cs[0])
                    away=next((x for x in cs if x.get("homeAway")=="away"),cs[1])
                    lname=data.get("leagues",[{}])[0].get("name") if data.get("leagues") else code
                    country,flag=classify_country(lname)
                    st=(comp.get("status",{}).get("type",{}) or {})
                    games.append({
                        "league":lname,
                        "leagueName":lname,
                        "country":country,
                        "flag":flag,
                        "home":(home.get("team",{}).get("displayName") or "Home")[:40],
                        "away":(away.get("team",{}).get("displayName") or "Away")[:40],
                        "score":st.get("shortDetail") or "TBD",
                        "live":st.get("state")=="in"
                    })

    # Deduplicate
    seen=set(); out=[]
    for g in games:
        k=(g["home"].lower(),g["away"].lower(),g["leagueName"].lower())
        if k not in seen:
            seen.add(k)
            out.append(g)
    print(f"Final games: {len(out)}")
    return out

@app.route("/api/games")
def api_games():
    games=fetch_espn()
    if not games:
        return jsonify({"games":[],"error":"No ESPN fixtures were returned. Check the server log and ESPN availability."})
    return jsonify({"games":games,"error":None,"date":datetime.now(BOTSWANA_TZ).strftime("%Y-%m-%d"),"count":len(games)})

@app.route("/api/prob")
def api_prob():
    home=request.args.get("home","Home").strip(); away=request.args.get("away","Away").strip()
    if not home or not away: return jsonify({"error":"Both home and away teams are required."}),400
    p=calc(home,away)
    html=f"""<div class='card'><div class='chead'>⚽ Full-Time <span class='free'>L5</span></div><div class='row3'><div><small>HOME</small><b>{p['hp']}%</b><div class='bar'><div style='width:{p['hp']}%'></div></div></div><div><small>DRAW</small><b>{p['dp']}%</b><div class='bar'><div style='width:{p['dp']}%'></div></div></div><div><small>AWAY</small><b>{p['ap']}%</b><div class='bar'><div style='width:{p['ap']}%'></div></div></div></div><small style='color:#8a96a8'>L5 {home}: W{p['hs']['wins']} D{p['hs']['draws']} | {p['hs']['avg_gf']:.1f} GF / {p['hs']['avg_ga']:.1f} GA<br>L5 {away}: W{p['aw']['wins']} D{p['aw']['draws']} | {p['aw']['avg_gf']:.1f} GF / {p['aw']['avg_ga']:.1f} GA</small></div><div class='card
