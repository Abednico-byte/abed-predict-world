from flask import Flask, render_template, render_template_string
import os, random

app = Flask(__name__)

def mg(n, teams):
    g=[]
    for _ in range(n):
        h,a=random.sample(teams,2)
        t=f"{random.randint(12,21)}:{random.choice(['00','15','30','45'])}"
        g.append(f"{h} vs {a} {t}")
    return g

TEAMS_FR=["Lyon","Monaco","Nice","PSG","Marseille","Lille","Lens","Brest","Auxerre","Angers"]
TEAMS_EN=["Arsenal","Man City","Liverpool","Chelsea"]
TEAMS_ES=["Real Madrid","Barcelona","Atletico","Sevilla"]
TEAMS_DE=["Bayern","Dortmund","Leverkusen","Leipzig"]

COUNTRIES={
 "France":[{"id":"fr_l1","n":"France - Ligue 1 (1st)","type":"PRO","games":mg(9,TEAMS_FR)}],
 "England":[{"id":"en_pl","n":"England - Premier League (1st)","type":"PRO","games":mg(9,TEAMS_EN)}],
 "Spain":[{"id":"es_lal","n":"Spain - LaLiga (1st)","type":"PRO","games":mg(8,TEAMS_ES)}],
 "Germany":[{"id":"de_bun","n":"Germany - Bundesliga (1st)","type":"PRO","games":mg(8,TEAMS_DE)}],
 "Botswana":[{"id":"bw_prem","n":"Botswana - Premier (1st)","type":"PRO","games":mg(8,["Gaborone Utd","Jwaneng Galaxy","Rollers"])}],
}

def find_league(lid):
    lid=lid.lower()
    for country, leagues in COUNTRIES.items():
        for l in leagues:
            if l["id"].lower()==lid:
                d=l.copy(); d["country"]=country; d["lid"]=l["id"]; return d
    return None

@app.route("/")
def home():
    return render_template("index.html", countries=COUNTRIES)

@app.route("/league/<lid>")
def league_page(lid):
    lg=find_league(lid)
    if not lg:
        return f"League {lid} not found",404
    try:
        return render_template("league.html", lg=lg)
    except:
        # fallback if league.html missing
        html="""<body style='background:#0e1625;color:#fff;font-family:sans-serif'><a href='/' style='color:#22c55e'> <- Back to World</a><h2>{{lg.country}} - {{lg.n}}</h2><div style='background:#1a2538;border-radius:12px;margin-top:12px'>{% for g in lg.games %}<a href='/game/{{lg.lid}}/{{loop.index0}}' style='display:flex;justify-content:space-between;padding:12px;border-bottom:1px solid #1f2e4a;color:#cbd5e1;text-decoration:none'><span>⚽ {{g}}</span><span style='color:#22c55e'>Predict -></span></a>{% endfor %}</div></body>"""
        return render_template_string(html, lg=lg)

@app.route("/game/<lid>/<int:gid>")
def game_page(lid,gid):
    lg=find_league(lid)
    if not lg:
        return f"League {lid} not found - check id",404
    if gid<0 or gid>=len(lg["games"]):
        return f"Game {gid} not found",404
    game=lg["games"][gid]
    try:
        return render_template("game.html", lg=lg, game=game, gid=gid)
    except Exception as e:
        # EMERGENCY FALLBACK - will ALWAYS load even if game.html is missing
        fallback="""
<!DOCTYPE html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'><title>{{game}}</title><style>
*{margin:0;padding:0;box-sizing:border-box}body{background:#0e1625;color:#cbd5e1;font-family:sans-serif;font-size:12px}
.top{background:#1a2538;padding:12px}.m{font-size:18px;font-weight:800;color:#fff;margin-top:6px}
.tabbar{display:flex;gap:18px;padding:10px 12px;background:#1a2538;border-bottom:1px solid #2a3a56}.t{color:#8da0bf;padding-bottom:4px}.t.a{color:#fff;border-bottom:3px solid #22c55e}
.subs{display:flex;gap:14px;padding:10px 12px;background:#1f2e4a;overflow:auto}.s{color:#8da0bf}.s.a{color:#fff;border-bottom:2px solid #22c55e;font-weight:700}
.box{background:#1e2d4a}.row{display:grid;grid-template-columns:60px 1fr 60px;padding:12px;border-bottom:1px solid #23324e;text-align:center}.val{font-weight:800;color:#fff;font-size:15px}.mid{font-size:10px;color:#8da0bf;text-transform:uppercase}
.lab{background:#0f172a;padding:8px;text-align:center;font-weight:800;color:#fff;margin-top:6px}
</style></head><body>
<div class='top'><a href='/league/{{lg.lid}}' style='color:#22c55e;text-decoration:none'> <- Back</a><div style='color:#8da0bf;margin-top:6px'>Sun 20th 14:00 🏆 {{lg.n}}</div><div class='m'>{{game}}</div></div>
<div class='tabbar'><div class='t'>Create</div><div class='t a'>Stats</div><div class='t'>Odds</div><div class='t'>Predictions</div></div>
<div class='subs'><div class='s a'>General</div><div class='s'>Goals</div><div class='s'>Corners</div><div class='s'>Cards</div></div>
<div class='box'>
<div class='row'><div class='val'>16</div><div class='mid'>LEAGUE POS.</div><div class='val'>9</div></div>
<div class='row'><div class='val'>2</div><div class='mid'>PLAYED</div><div class='val'>2</div></div>
<div class='row'><div class='val'>50%</div><div class='mid'>WIN %</div><div class='val'>50%</div></div>
<div class='row'><div class='val'>0%</div><div class='mid'>DRAW %</div><div class='val'>50%</div></div>
<div class='row'><div class='val'>3</div><div class='mid'>POINTS</div><div class='val'>4</div></div>
<div class='row'><div class='val'>29.00</div><div class='mid'>SHOTS (AVG)</div><div class='val'>35.50</div></div>
</div>
<div class='lab'>Total Goals %</div>
<div class='box'>
<div class='row'><div class='val'>100%</div><div class='mid'>+0.5 GOALS %</div><div class='val'>100%</div></div>
<div class='row'><div class='val'>100%</div><div class='mid'>+2.5 GOALS %</div><div class='val'>100%</div></div>
<div class='row'><div class='val'>0%</div><div class='mid'>BTTS %</div><div class='val'>100%</div></div>
</div>
<div class='lab'>Corners</div>
<div class='box'>
<div class='row'><div class='val'>12.00</div><div class='mid'>TOTAL CORNERS PG</div><div class='val'>9.00</div></div>
<div class='row'><div class='val'>11</div><div class='mid'>FOR TOTAL</div><div class='val'>7</div></div>
</div>
<div style='padding:12px;color:#8da0bf;font-size:10px'>Loaded fallback because game.html missing. Error: {{err}}</div>
</body></html>
"""
        return render_template_string(fallback, lg=lg, game=game, err=str(e))

@app.route("/filters")
def filters_page():
    try:
        return render_template("filters.html")
    except:
        return "<h3 style='color:white;background:#0e1625'>Filters loading... create filters.html file</h3><a href='/'>Home</a>"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
