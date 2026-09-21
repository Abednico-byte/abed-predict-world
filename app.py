from flask import Flask, request
import requests, os, time
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
app = Flask(__name__)
ESPN_HEADERS = {"User-Agent":"Mozilla/5.0","Referer":"https://abed-predict-world.onrender.com"}

COUNTRIES = [
    ("USA","usa.1","Inter Miami"),("South Africa","rsa.1","Mamelodi Sundowns"),
    ("England","eng.1","Man City"),("Germany","ger.1","Bayern Munich"),
    ("Italy","ita.1","Inter Milan"),("Sweden","swe.1","Malmo FF"),
    ("Turkey","tur.1","Galatasaray"),("Netherlands","ned.1","Ajax"),
    ("France","fra.1","PSG"),("Switzerland","swi.1","Young Boys"),
    ("Saudi Arabia","ksa.1","Al Hilal"),("China","chn.1","Shanghai Port"),
    ("Azerbaijan","aze.1","Qarabag"),("Denmark","den.1","Copenhagen"),
    ("Croatia","cro.1","Dinamo Zagreb"),("Greece","gre.1","Olympiacos"),
    ("Ireland","irl.1","Shamrock Rovers"),("Norway","nor.1","Bodo Glimt"),
    ("Portugal","por.1","Benfica"),("Ukraine","ukr.1","Shakhtar"),
    ("Spain","esp.1","Real Madrid"),("Euro Cups","uefa.champions","Real Madrid"),
    ("FIFA Competition","fifa.world","Brazil"),
]

SUB_TABS_DEF = {
    "USA":["MLS - Pro","USL - Pro 2","Amateur","US Open Cup - Cup"],
    "South Africa":["PSL - Pro","Motsepe - Pro 2","Amateur","Nedbank Cup - Cup"],
    "England":["Premier League - Pro","Championship - Pro 2","League One - Pro 3","League Two - Amateur","National League - Amateur 2","FA Cup - Cup","League Cup - Cup"],
    "Germany":["Bundesliga - Pro","2. Bundesliga - Pro 2","3. Liga - Amateur","DFB-Pokal - Cup"],
    "Spain":["LaLiga - Pro","LaLiga 2 - Pro 2","Amateur","Copa del Rey - Cup"],
    "Euro Cups":["Champions League","Europa League","Conference League"],
    "FIFA Competition":["World Cup","Qualifiers","Friendly"],
}
for c in COUNTRIES:
    if c[0] not in SUB_TABS_DEF:
        SUB_TABS_DEF[c[0]]=["Premier - Pro","Second - Pro 2","Amateur","Cup"]

CACHE={"t":0,"data":{}, "date":""}

def parse_kickoff(iso_str):
    try:
        # ESPN iso like 2026-09-21T19:00:00Z -> to CAT (UTC+2 Gaborone)
        dt=datetime.fromisoformat(iso_str.replace('Z','+00:00'))
        dt_cat=dt+timedelta(hours=2) # CAT Botswana
        return dt_cat.strftime("%H:%M CAT"), dt_cat.strftime("%Y-%m-%d %H:%M")
    except:
        return "--:--", ""

def get_correct_dual(date_str):
    yyyymmdd = date_str.replace('-','')
    if CACHE["date"]==date_str and time.time()-CACHE["t"]<90 and CACHE["data"]:
        return CACHE["data"]
    out={c[0]:[] for c in COUNTRIES}
    try:
        url=f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={yyyymmdd}"
        r=requests.get(url, headers=ESPN_HEADERS, timeout=3)
        if r.status_code==200:
            for ev in r.json().get('events',[])[:150]:
                comp=ev.get('competitions',[{}])[0]; comps=comp.get('competitors',[])
                if len(comps)<2: continue
                h=comps[0] if comps[0].get('homeAway')=='home' else comps[1]
                a=comps[1] if comps[0].get('homeAway')=='home' else comps[0]
                hs=h.get('score',''); aws=a.get('score','')
                short=ev.get('status',{}).get('type',{}).get('shortDetail','') or 'FT'
                iso_date=ev.get('date','')
                kickoff_time, kickoff_full = parse_kickoff(iso_date)
                # score logic
                if hs!='' and aws!='':
                    score=f"{hs}-{aws} {short}"
                else:
                    # PREMATCH with kickoff time
                    score=f"{kickoff_time} PREMATCH" if kickoff_time!="--:--" else f"{short} PREMATCH"
                league=ev.get('leagues',[{}])[0].get('name','') or ''
                lname=league.lower()
                cname=None
                if 'england' in lname or 'premier league' in lname or 'championship' in lname or 'fa cup' in lname: cname="England"
                elif 'bundesliga' in lname: cname="Germany"
                elif 'la liga' in lname or 'copa del rey' in lname: cname="Spain"
                elif 'serie a' in lname or 'serie b' in lname or 'coppa' in lname: cname="Italy"
                elif 'ligue' in lname: cname="France"
                elif 'eredivisie' in lname: cname="Netherlands"
                elif 'mls' in lname or 'major league' in lname or 'usl' in lname: cname="USA"
                elif 'super lig' in lname: cname="Turkey"
                elif 'allsvenskan' in lname: cname="Sweden"
                elif 'switzerland' in lname or 'swiss' in lname: cname="Switzerland"
                elif 'saudi' in lname: cname="Saudi Arabia"
                elif 'china' in lname: cname="China"
                elif 'azerbaijan' in lname: cname="Azerbaijan"
                elif 'denmark' in lname or 'superliga' in lname: cname="Denmark"
                elif 'croatia' in lname: cname="Croatia"
                elif 'greece' in lname: cname="Greece"
                elif 'ireland' in lname: cname="Ireland"
                elif 'eliteserien' in lname or 'norway' in lname: cname="Norway"
                elif 'portugal' in lname or 'primeira' in lname: cname="Portugal"
                elif 'ukraine' in lname: cname="Ukraine"
                elif 'champions' in lname or 'europa' in lname: cname="Euro Cups"
                elif 'world cup' in lname or 'fifa' in lname: cname="FIFA Competition"
                elif 'psl' in lname or 'south africa' in lname: cname="South Africa"
                if cname and cname in out:
                    tier="Pro"
                    if 'championship' in lname or '2.' in lname: tier="Pro 2"
                    elif 'cup' in lname: tier="Cup"
                    elif 'national' in lname: tier="Amateur"
                    out[cname].append({"home":h.get('team',{}).get('displayName',''),"away":a.get('team',{}).get('displayName',''),"score":score,"league":league,"tier":tier,"id":ev.get('id',''),"kickoff":kickoff_time,"kickoff_full":kickoff_full,"iso":iso_date})
    except Exception as e:
        print(e)
    CACHE["data"]=out; CACHE["t"]=time.time(); CACHE["date"]=date_str
    return out

@app.route('/')
def home():
    day=request.args.get('day','0')
    date_str=(datetime(2026,9,21)+timedelta(days=int(day))).strftime("%Y-%m-%d")
    data=get_correct_dual(date_str)
    tabs="".join([f'<a style="background:{"#00c853" if str(i)==day else "#242F44"};color:{"black" if str(i)==day else "white"};padding:6px 10px;border-radius:20px;text-decoration:none;margin-right:5px;font-size:11px" href="/?day={i}">{i} 09/{21+int(i)}</a>' for i in range(7)])
    html=f'<div style="background:#00c853;color:black;padding:10px;font-weight:bold">ABED PREDICT WORLD - {date_str} - 23 Countries - KICKOFF TIME CAT</div>'
    html+=f'<div style="padding:10px;overflow-x:auto;white-space:nowrap;background:#0f1623;position:sticky;top:0;z-index:10">{tabs}</div>'
    for cname,_,example in COUNTRIES:
        games=data.get(cname,[])
        sub_tabs=SUB_TABS_DEF.get(cname,["Premier - Pro","Cup"])
        html+=f'''
        <div onclick="toggleCountry('{cname}')" style="background:#0f1623;padding:10px 12px;color:#00c853;font-size:13px;font-weight:bold;cursor:pointer;border-top:1px solid #1e2a3a;display:flex;justify-content:space-between">
            <span>{cname} - {example} etc ({len(games)} games {date_str})</span><span id="arrow-{cname}">▼</span>
        </div>
        <div id="country-{cname}" style="display:none">
            <div style="background:#1a2332;padding:6px 8px;overflow-x:auto;white-space:nowrap;display:flex;gap:4px">
        '''
        for j, st in enumerate(sub_tabs):
            html+=f'<button onclick="filterLeague(\'{cname}\',\'{st.split(" - ")[0]}\',this)" style="background:{"#00c853" if j==0 else "#242F44"};color:{"black" if j==0 else "white"};border:none;padding:5px 10px;border-radius:15px;font-size:10px">{st}</button>'
        html+='</div><div id="games-'+cname+'">'
        if not games:
            html+=f'<div style="background:#1e2a3a;padding:12px;font-size:12px;color:#888">No games {cname} on {date_str} - Try 09/26 Saturday</div>'
        for g in games[:20]:
            h_enc=quote(g["home"]); a_enc=quote(g["away"]); l_enc=quote(g["league"])
            link=f"/match?home={h_enc}&away={a_enc}&league={l_enc}&score={quote(g['score'])}&country={quote(cname)}&date={date_str}&id={g['id']}&kickoff={quote(g['kickoff_full'])}"
            # KICKOFF TIME ADDED ON EACH MATCH
            html+=f'<a href="{link}" style="text-decoration:none;color:white"><div style="background:#1e2a3a;border-bottom:1px solid #0f1623;padding:12px;display:flex;justify-content:space-between;font-size:13px"><span><b style="color:#00c853">{g["kickoff"]}</b> - {g["home"]} vs {g["away"]} - {g["league"]} ({g["tier"]})</span><span style="color:#00c853;white-space:nowrap">{g["score"]} →</span></div></a>'
        html+='</div></div>'
    js='''<script>
    function toggleCountry(name){
        var el=document.getElementById('country-'+name);var arrow=document.getElementById('arrow-'+name);
        if(el.style.display==='none'){
            document.querySelectorAll('[id^="country-"]').forEach(function(d){d.style.display='none'});
            document.querySelectorAll('[id^="arrow-"]').forEach(function(a){a.innerText='▼'});
            el.style.display='block';arrow.innerText='▲';
        }else{el.style.display='none';arrow.innerText='▼';}
    }
    function filterLeague(c,kw,btn){btn.parentElement.querySelectorAll('button').forEach(function(b){b.style.background='#242F44';b.style.color='white';});btn.style.background='#00c853';btn.style.color='black';}
    </script>'''
    return f"<html><head><meta name='viewport' content='width=device-width'></head><body style='background:#0f1623;color:white;font-family:Arial;margin:0'>{html}{js}</body></html>"

@app.route('/match')
def match_page():
    home=unquote(request.args.get('home','')); away=unquote(request.args.get('away','')); league=unquote(request.args.get('league','')); score=unquote(request.args.get('score','')); country=unquote(request.args.get('country','')); date=request.args.get('date',''); mid=request.args.get('id',''); kickoff=unquote(request.args.get('kickoff',''))
    return f"<html><head><meta name='viewport' content='width=device-width'></head><body style='background:#0f1623;color:white;font-family:Arial;margin:0'><div style='background:#00c853;color:black;padding:10px'><a href='/' style='color:black;text-decoration:none'>← BACK</a> - {home} vs {away} - KICKOFF {kickoff}</div><div style='padding:12px'><div style='background:#1e2a3a;padding:15px;border-left:4px solid #00c853;margin-bottom:10px'><b>{home} vs {away}</b><br>{league} - {country}<br>🕐 Kickoff: <b style='color:#00c853'>{kickoff} CAT Gaborone</b><br>Score: {score} - ID {mid}<br>Date: {date}</div><div style='background:#242F44;padding:10px;border-radius:10px'>All prompts under game with kickoff time correct by date and country.</div></div></body></html>"

if __name__ == '__main__':
    port=int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
