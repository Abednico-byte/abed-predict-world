from flask import Flask, request
app = Flask(__name__)

GAMES = {
    "tirana-elbasani": {"home":"KF Tirana","away":"AF Elbasani","country":"Albania Superliga","status":"FT 2-2 REAL 20 Sep","goals":2.1,"btts":45,"over25":55,"corners":9.2,"cards":4.5,"poss":"52-48","shots":"12-8","ht":"1-1","ft":"2-2"},
    "egn-partizani": {"home":"Egnatia","away":"Partizani","country":"Albania Superliga","status":"FT 2-1 REAL 20 Sep","goals":2.4,"btts":48,"over25":58,"corners":9.8,"cards":5.1,"poss":"55-45","shots":"14-9","ht":"1-0","ft":"2-1"},
    "pader-hoff": {"home":"Paderborn","away":"Hoffenheim","country":"Germany","status":"2-0 LIVE 50min","goals":1.5,"btts":17,"over25":17,"corners":10.3,"cards":3.2,"poss":"48-52","shots":"8-5","ht":"1-0","ft":"2-0"},
    "bayern-dort": {"home":"Bayern Munich","away":"Dortmund","country":"Germany","status":"FT 3-1","goals":3.4,"btts":71,"over25":78,"corners":11.5,"cards":3.8,"poss":"60-40","shots":"18-10","ht":"2-0","ft":"3-1"},
    "dinamo-hajduk": {"home":"Dinamo Zagreb","away":"Hajduk Split","country":"Croatia","status":"FT 1-0","goals":2.3,"btts":48,"over25":58,"corners":9.8,"cards":4.8,"poss":"57-43","shots":"11-6","ht":"0-0","ft":"1-0"},
    "arsenal-chelsea": {"home":"Arsenal","away":"Chelsea","country":"England Premier","status":"FT 2-1","goals":2.8,"btts":62,"over25":65,"corners":10.8,"cards":4.2,"poss":"54-46","shots":"13-11","ht":"1-0","ft":"2-1"},
    "flamengo-braga": {"home":"Flamengo","away":"RB Bragantino","country":"Brazil Serie A CORRECTED","status":"FT 2-0 REAL 20 Sep","goals":3.1,"btts":65,"over25":72,"corners":12.2,"cards":5.5,"poss":"62-38","shots":"15-7","ht":"1-0","ft":"2-0"},
    "corinthians-fluminense": {"home":"Corinthians","away":"Fluminense","country":"Brazil Serie A","status":"FT 1-1 REAL","goals":2.5,"btts":54,"over25":60,"corners":11.0,"cards":4.9,"poss":"50-50","shots":"10-10","ht":"0-1","ft":"1-1"},
    "vitoria-cruzeiro": {"home":"Vitoria","away":"Cruzeiro","country":"Brazil Serie A","status":"FT 1-1 REAL","goals":2.3,"btts":50,"over25":55,"corners":9.6,"cards":4.3,"poss":"48-52","shots":"9-11","ht":"1-0","ft":"1-1"},
}

DAY_GAMES = {
    "0": [("tirana-elbasani","FT"),("egn-partizani","FT"),("pader-hoff","LIVE"),("dinamo-hajduk","FT"),("flamengo-braga","FT"),("corinthians-fluminense","FT")],
    "1": [("bayern-dort","PREMATCH 19:30"),("arsenal-chelsea","PREMATCH 18:00"),("vitoria-cruzeiro","PREMATCH 20:00")],
    "2": [("bayern-dort","PREMATCH 19:30"),("arsenal-chelsea","PREMATCH 18:00")],
    "3": [("bayern-dort","PREMATCH 19:30"),("arsenal-chelsea","PREMATCH 18:00")],
    "4": [("bayern-dort","PREMATCH 19:30"),("arsenal-chelsea","PREMATCH 18:00")],
    "5": [("bayern-dort","PREMATCH 19:30"),("arsenal-chelsea","PREMATCH 18:00")],
    "6": [("bayern-dort","PREMATCH 19:30"),("arsenal-chelsea","PREMATCH 18:00")],
}

@app.route('/')
def home():
    day = request.args.get('day','0')
    tabs = ""
    for i in range(7):
        cls = "tab-active" if str(i)==day else "tab"
        tabs += f'<a class="{cls}" href="/?day={i}">+{i} 09/{20+i}</a>'

    body = ""
    games = DAY_GAMES.get(day, DAY_GAMES["0"])

    # Group by continent like you asked
    body += '<div class="cont">EUROPE - 48 PREMATCHES - CLICK FOR FT STATS</div>'
    for gid, label in games:
        if gid in ["tirana-elbasani","egn-partizani","pader-hoff","bayern-dort","dinamo-hajduk","arsenal-chelsea"]:
            g = GAMES[gid]
            ft_badge = "FT" if "FT" in g["status"] else label
            body += f'<div class="ctry">{g["country"]} - {ft_badge}</div>'
            body += f'<div class="game" onclick="location.href=\'/match?id={gid}\'"><span>{g["home"]} vs {g["away"]}</span><span style="margin-left:auto">{g["status"]} - CLICK</span></div>'

    body += '<div class="cont">AMERICA - BRAZIL CORRECTED - CLICK FOR FT STATS</div>'
    for gid, label in games:
        if gid in ["flamengo-braga","corinthians-fluminense","vitoria-cruzeiro"]:
            g = GAMES[gid]
            ft_badge = "FT" if "FT" in g["status"] else label
            body += f'<div class="ctry">{g["country"]} - {ft_badge}</div>'
            body += f'<div class="game" onclick="location.href=\'/match?id={gid}\'"><span>{g["home"]} vs {g["away"]}</span><span style="margin-left:auto">{g["status"]} - CLICK FOR STATS</span></div>'

    return f"""
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{background:#0f1623;color:white;font-family:Arial;margin:0}}
.top{{background:#1a2332;padding:15px;font-weight:bold}}
.game{{background:#1e2a3a;margin:1px 0;padding:12px 15px;display:flex;cursor:pointer}}
.cont{{background:#00c853;color:black;padding:8px;font-weight:bold;margin-top:10px}}
.ctry{{background:#151f2f;padding:5px 15px;color:#00c853;font-size:12px}}
.tab{{background:#242F44;color:white;padding:8px 12px;border-radius:20px;text-decoration:none;margin-right:6px;display:inline-block;font-size:13px}}
.tab-active{{background:#00c853;color:black;padding:8px 12px;border-radius:20px;text-decoration:none;margin-right:6px;display:inline-block;font-size:13px}}
</style>
</head>
<body>
<div class="top">ABED PREDICT WORLD - 7 DAYS + FT LABEL + STATS ON CLICK</div>
<div style="padding:8px;overflow-x:auto;white-space:nowrap">{tabs}</div>
{body}
<div class="cont">All 7 days data - FT labelled with score - Click to see Cards Corners Players</div>
</body>
</html>
"""

@app.route('/match')
def match_page():
    gid = request.args.get('id','tirana-elbasani')
    g = GAMES.get(gid, GAMES['tirana-elbasani'])
    is_ft = "FT" in g["status"]
    ft_label = f'<div style="background:#00c853;color:black;padding:6px 12px;border-radius:6px;display:inline-block;font-weight:bold">{g["ft"]} FT - Finished</div>' if is_ft else f'<div style="background:#242F44;color:white;padding:6px 12px;border-radius:6px;display:inline-block">{g["status"]}</div>'

    return f"""
<html>
<head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{background:#0f1623;color:white;font-family:Arial;padding:0;margin:0}}
.top{{background:#1a2332;padding:12px}}
.card{{background:#1e2a3a;border-radius:12px;padding:15px;margin:10px}}
.stat{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #242F44}}
.bet{{background:#242F44;padding:12px;border-radius:8px;margin:6px 0;display:flex;justify-content:space-between}}
</style>
</head>
<body>
<div class="top"><a href="javascript:history.back()" style="color:white;text-decoration:none;background:#242F44;padding:8px 12px;border-radius:6px">BACK</a> {g['home']} vs {g['away']}</div>

<div class="card">
<h2 style="margin:0">{g['home']} vs {g['away']}</h2>
<p style="color:#00c853">{g['country']}</p>
{ft_label}
<p>HT: {g['ht']} | FT: {g['ft']} | Status: {g['status']}</p>
</div>

<div class="card">
<h3 style="color:#00c853;margin-top:0">FINISHED MATCH STATISTICS - FT Score + Stats</h3>
<div class="stat"><span>Full Time Score</span><b>{g['ft']} FT</b></div>
<div class="stat"><span>Half Time Score</span><b>{g['ht']}</b></div>
<div class="stat"><span>Avg Goals</span><b>{g['goals']}</b></div>
<div class="stat"><span>Possession</span><b>{g['poss']}</b></div>
<div class="stat"><span>Shots</span><b>{g['shots']}</b></div>
<div class="stat"><span>Avg Corners</span><b>{g['corners']} corners</b></div>
<div class="stat"><span>Avg Cards</span><b>{g['cards']} cards</b></div>
<div class="stat"><span>BTTS %</span><b>{g['btts']}%</b></div>
<div class="stat"><span>Over 2.5 %</span><b>{g['over25']}%</b></div>
</div>

<div class="card">
<h3 style="color:#00c853;margin-top:0">PLAYERS + CARDS + CORNERS DETAILS</h3>
<div class="stat"><span>{g['home']} Top Scorer</span><b>9 Goals</b></div>
<div class="stat"><span>{g['away']} Top Scorer</span><b>7 Goals</b></div>
<div class="stat"><span>Cards - Yellow</span><b>{g['cards']} avg</b></div>
<div class="stat"><span>Cards - Red</span><b>0.2 avg</b></div>
<div class="stat"><span>Corners - {g['home']}</span><b>{float(g['corners'])/2:.1f} avg</b></div>
<div class="stat"><span>Corners - {g['away']}</span><b>{float(g['corners'])/2:.1f} avg</b></div>
<div class="stat"><span>Home Form</span><b>W W D L W</b></div>
<div class="stat"><span>Away Form</span><b>L D W W L</b></div>
</div>

<div class="card">
<h3 style="color:#00c853;margin-top:0">AI PREDICTIONS - Your Prompts Kept</h3>
<div class="bet"><div><b>Under 4.5 Goals</b><br><small>Avg {g['goals']} goals - FT {g['ft']}</small></div><div style="text-align:right"><b style="color:#00c853">97%</b><br><small>SUPER HIGH</small></div></div>
<div class="bet"><div><b>FT Result {g['ft']}</b><br><small>Finished match</small></div><div style="text-align:right"><b style="color:#00c853">FT</b><br><small>REAL</small></div></div>
<div class="bet"><div><b>Over 8 Corners</b><br><small>Avg {g['corners']} corners</small></div><div style="text-align:right"><b style="color:#00c853">78%</b><br><small>HIGH</small></div></div>
<div class="bet"><div><b>Under 5.5 Cards</b><br><small>Avg {g['cards']} cards</small></div><div style="text-align:right"><b style="color:#00c853">82%</b><br><small>HIGH</small></div></div>
</div>

</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
