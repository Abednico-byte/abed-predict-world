from flask import Flask, render_template, jsonify
import os, random
from datetime import datetime
app = Flask(__name__)

def make_games(n, teams):
    g=[]
    for i in range(n):
        h,a = random.sample(teams,2)
        t=f"{random.randint(8,21)}:{random.choice(['00','15','30','45'])}"
        g.append(f"{h} vs {a} {t}")
    return g
# BASE TEAMS POOL
T={"es":["Real Madrid","Barcelona","Atletico","Sevilla","Valencia","Villarreal","Betis","Girona","Bilbao","Sociedad"],"es2":["Granada","Leganes","Eibar","Almeria","Valladolid","Espanyol","Oviedo","Zaragoza"],"gr":["Olympiacos","Panathinaikos","AEK","PAOK","Aris","Volos","Panetolikos"],"se":["Malmo","AIK","Djurgarden","Hacken","Hammarby","Elfsborg","Goteborg","Norrkoping"],"mx":["America","Chivas","Cruz Azul","Pumas","Tigres","Monterrey","Atlas","Santos"],"us":["Inter Miami","LAFC","LA Galaxy","Columbus Crew","Atlanta Utd","NYCFC","Seattle","Cincinnati"],"br":["Flamengo","Palmeiras","Corinthians","Santos","Sao Paulo","Fluminense","Botafogo","Gremio"],"ar":["River Plate","Boca Juniors","Racing","Independiente","San Lorenzo","Rosario"],"bw":["Gaborone Utd","Jwaneng Galaxy","Rollers","Orapa Utd","BDF XI","Masitaoka","Morupule","Police XI"],"za":["Sundowns","Chiefs","Pirates","SuperSport","Cape Town City","Stellies","AmaZulu"],"eg":["Al Ahly","Zamalek","Pyramids","Esperance","Wydad","Raja","Simba","Yanga"],"eu":["Bayern","Dortmund","Leverkusen","Arsenal","Man City","Liverpool","Inter","Milan","Juventus","PSG","Marseille","Ajax","PSV","Benfica","Porto"],"as":["Al Nassr","Al Hilal","Al Ittihad","Urawa","Kawasaki","Seoul","Jeonbuk","Persepolis","Mumbai City"]}

WORLD=[
# SPAIN - YOU ASKED
{"id":"es_laliga","n":"Spain - LaLiga","c":"EUROPE PRO","f":10,"games":make_games(10,T["es"])},
{"id":"es_laliga2","n":"Spain - LaLiga 2","c":"EUROPE PRO 2","f":11,"games":make_games(11,T["es2"])},
{"id":"es_rfef","n":"Spain - Primera RFEF (Amateur)","c":"EUROPE AMATEUR","f":12,"games":make_games(12,["Betis B","Sevilla At","Alcoyano","Marbella","Ibiza","Antequera","Merida","Alcorcon"])},
{"id":"es_copa","n":"Spain - Copa del Rey (Cup)","c":"CUP","f":8,"games":make_games(8,T["es"]+T["es2"])},

# GREECE
{"id":"gr_sl","n":"Greece - Super League","c":"EUROPE PRO","f":8,"games":make_games(8,T["gr"])},
{"id":"gr_sl2","n":"Greece - Super League 2","c":"EUROPE PRO 2","f":10,"games":make_games(10,["Larissa","Kallithea","Levadiakos","Kalamata","Ionikos","Chania"])},
{"id":"gr_cup","n":"Greece - Cup","c":"CUP","f":6,"games":make_games(6,T["gr"])},

# SWEDEN
{"id":"se_allsv","n":"Sweden - Allsvenskan","c":"EUROPE PRO","f":8,"games":make_games(8,T["se"])},
{"id":"se_super","n":"Sweden - Superettan","c":"EUROPE PRO 2","f":10,"games":make_games(10,["Osters","GAIS","Orebro","Vasteras","Helsingborg","Brage"])},
{"id":"se_ettan","n":"Sweden - Ettan (Amateur)","c":"EUROPE AMATEUR","f":12,"games":make_games(12,["Trollhattan","Falkenberg","Ljungskile","Sollentuna","IFK Lulea","Husqvarna"])},
{"id":"se_cup","n":"Sweden - Svenska Cupen","c":"CUP","f":8,"games":make_games(8,T["se"])},

# ALL AMERICAN LEAGUES
{"id":"us_mls","n":"USA - MLS","c":"AMERICA PRO","f":14,"games":make_games(14,T["us"])},
{"id":"us_usl","n":"USA - USL Championship (2nd)","c":"AMERICA PRO 2","f":12,"games":make_games(12,["Indy Eleven","Sacramento","Louisville","Detroit City","Charleston","Phoenix Rising"])},
{"id":"us_open","n":"USA - US Open Cup (Cup)","c":"CUP","f":10,"games":make_games(10,T["us"])},
{"id":"mx_liga","n":"Mexico - Liga MX","c":"AMERICA PRO","f":9,"games":make_games(9,T["mx"])},
{"id":"mx_exp","n":"Mexico - Expansion (Amateur)","c":"AMERICA AMATEUR","f":10,"games":make_games(10,["Cancun","Celaya","Leones Negros","Tapatío","Atlante","Morelia"])},
{"id":"br_a","n":"Brazil - Serie A","c":"AMERICA PRO","f":10,"games":make_games(10,T["br"])},
{"id":"br_b","n":"Brazil - Serie B","c":"AMERICA PRO 2","f":12,"games":make_games(12,["Santos","Sport Recife","Goias","Vila Nova","Coritiba","America MG"])},
{"id":"ar_liga","n":"Argentina - Liga Profesional","c":"AMERICA PRO","f":14,"games":make_games(14,T["ar"])},
{"id":"ar_nac","n":"Argentina - Primera Nacional (2nd)","c":"AMERICA PRO 2","f":12,"games":make_games(12,["San Martin Tuc","Aldosivi","Colon","Nueva Chicago","Gimnasia Jujuy"])},
{"id":"co","n":"Colombia - Primera A","c":"AMERICA PRO","f":10,"games":make_games(10,["Atletico Nacional","Millonarios","Junior","America Cali","Tolima"])},
{"id":"cl","n":"Chile - Primera","c":"AMERICA PRO","f":8,"games":make_games(8,["Colo Colo","U de Chile","Catolica","Union Espanola"])},
{"id":"pe","n":"Peru - Liga 1","c":"AMERICA PRO","f":8,"games":make_games(8,["Alianza Lima","Universitario","Sporting Cristal","Melgar"])},
{"id":"libert","n":"Copa Libertadores (Cup)","c":"CUP AMERICA","f":8,"games":make_games(8,T["br"]+T["ar"])},

# ALL AFRICAN LEAGUES
{"id":"bw_prem","n":"Botswana - Premier League","c":"AFRICA PRO","f":8,"games":make_games(8,T["bw"])},
{"id":"bw_first","n":"Botswana - First Division (Amateur)","c":"AFRICA AMATEUR","f":12,"games":make_games(12,["BMC","Extension Gunners","Black Forest","Mogoditshane","Chiefs","Tlokweng Utd","Holy Ghost"])},
{"id":"za_psl","n":"South Africa - PSL","c":"AFRICA PRO","f":8,"games":make_games(8,T["za"])},
{"id":"za_mot","n":"South Africa - Motsepe (Amateur)","c":"AFRICA AMATEUR","f":12,"games":make_games(12,["Orbit College","Pretoria Callies","Hungry Lions","Upington","Milford","Baroka"])},
{"id":"eg_prem","n":"Egypt - Premier League","c":"AFRICA PRO","f":10,"games":make_games(10,["Al Ahly","Zamalek","Pyramids","Al Masry","Future FC","ENPPI"])},
{"id":"ma_bot","n":"Morocco - Botola Pro","c":"AFRICA PRO","f":8,"games":make_games(8,["Wydad","Raja","FAR Rabat","RS Berkane","Maghreb Fes"])},
{"id":"ng_npfl","n":"Nigeria - NPFL","c":"AFRICA PRO","f":10,"games":make_games(10,["Enyimba","Rangers","Remo Stars","Kano Pillars","Plateau Utd"])},
{"id":"ke_prem","n":"Kenya - FKF Premier","c":"AFRICA PRO","f":8,"games":make_games(8,["Gor Mahia","Tusker","AFC Leopards","Kenya Police"])},
{"id":"tz","n":"Tanzania - Ligi Kuu","c":"AFRICA PRO","f":8,"games":make_games(8,["Simba","Yanga","Azam","Namungo"])},
{"id":"gh","n":"Ghana - Premier","c":"AFRICA PRO","f":8,"games":make_games(8,["Hearts of Oak","Asante Kotoko","Medeama","Great Olympics"])},
{"id":"zm","n":"Zambia - Super League","c":"AFRICA PRO","f":8,"games":make_games(8,["Power Dynamos","ZESCO","Nkana","Red Arrows"])},
{"id":"caf_cl","n":"CAF Champions League (Cup)","c":"CUP AFRICA","f":8,"games":make_games(8,T["eg"])},

# ALL EUROPEAN LEAGUES
{"id":"en_pl","n":"England - Premier League","c":"EUROPE PRO","f":10,"games":make_games(10,["Arsenal","Man City","Liverpool","Chelsea","Man Utd","Tottenham"])},
{"id":"en_ch","n":"England - Championship","c":"EUROPE PRO 2","f":12,"games":make_games(12,["Leeds","Leicester","Southampton","Ipswich","Middlesbrough"])},
{"id":"en_nat","n":"England - National League (Amateur)","c":"EUROPE AMATEUR","f":12,"games":make_games(12,["Wrexham","Notts Co","Chesterfield","Barnet","Oldham","York"])},
{"id":"en_fa","n":"England - FA Cup","c":"CUP","f":12,"games":make_games(12,["Arsenal","Man City","Liverpool","Wrexham","Notts Co","Chesterfield"])},
{"id":"de_bun","n":"Germany - Bundesliga","c":"EUROPE PRO","f":9,"games":make_games(9,["Bayern","Dortmund","Leverkusen","Leipzig","Stuttgart","Frankfurt"])},
{"id":"de_bun2","n":"Germany - 2. Bundesliga","c":"EUROPE PRO 2","f":9,"games":make_games(9,["Hamburg","Schalke","Hertha","Kaiserslautern","Hannover"])},
{"id":"de_reg","n":"Germany - Regionalliga (Amateur)","c":"EUROPE AMATEUR","f":14,"games":make_games(14,["Aachen","Wuppertal","Chemnitzer","Kickers Offenbach","Bayern II"])},
{"id":"it_a","n":"Italy - Serie A","c":"EUROPE PRO","f":10,"games":make_games(10,["Inter","Milan","Napoli","Juventus","Roma","Lazio","Atalanta"])},
{"id":"it_c","n":"Italy - Serie C (Amateur)","c":"EUROPE AMATEUR","f":12,"games":make_games(12,["Juventus U23","Catania","Benevento","Crotone","Perugia"])},
{"id":"fr_l1","n":"France - Ligue 1","c":"EUROPE PRO","f":9,"games":make_games(9,["PSG","Marseille","Lyon","Monaco","Lille","Nice"])},
{"id":"nl_er","n":"Netherlands - Eredivisie","c":"EUROPE PRO","f":9,"games":make_games(9,["Ajax","PSV","Feyenoord","AZ Alkmaar","Twente"])},
{"id":"pt_p","n":"Portugal - Primeira Liga","c":"EUROPE PRO","f":9,"games":make_games(9,["Benfica","Porto","Sporting","Braga","Guimaraes"])},
{"id":"tr_s","n":"Turkey - Super Lig","c":"EUROPE PRO","f":10,"games":make_games(10,["Galatasaray","Fenerbahce","Besiktas","Trabzonspor","Basaksehir"])},
{"id":"be","n":"Belgium - Jupiler Pro","c":"EUROPE PRO","f":8,"games":make_games(8,["Club Brugge","Anderlecht","Genk","Union SG","Antwerp"])},
{"id":"ucl","n":"UEFA Champions League (Cup)","c":"CUP EUROPE","f":12,"games":make_games(12,T["eu"])},
{"id":"uel","n":"UEFA Europa League (Cup)","c":"CUP EUROPE","f":12,"games":make_games(12,T["eu"])},

# ALL ASIAN LEAGUES
{"id":"sa_pro","n":"Saudi Arabia - Pro League","c":"ASIA PRO","f":9,"games":make_games(9,["Al Nassr","Al Hilal","Al Ittihad","Al Ahli","Al Ettifaq"])},
{"id":"jp_j1","n":"Japan - J1 League","c":"ASIA PRO","f":10,"games":make_games(10,["Urawa","Kawasaki","Yokohama F Marinos","Vissel Kobe","Kashima"])},
{"id":"kr_k1","n":"South Korea - K League 1","c":"ASIA PRO","f":8,"games":make_games(8,["Ulsan","Jeonbuk","Seoul FC","Pohang","Daegu"])},
{"id":"in_isl","n":"India - ISL","c":"ASIA PRO","f":8,"games":make_games(8,["Mumbai City","Mohun Bagan","Kerala Blasters","Bengaluru","Goa"])},
{"id":"ae","n":"UAE - Pro League","c":"ASIA PRO","f":8,"games":make_games(8,["Al Ain","Al Wahda","Shabab Al Ahli","Sharjah"])},
{"id":"afc_cl","n":"AFC Champions League (Cup)","c":"CUP ASIA","f":8,"games":make_games(8,T["as"])},
]

def find_league(lid):
    for l in WORLD:
        if l["id"]==lid: return l
    return None

def predict_for(game):
    random.seed(hash(game)%100000)
    h=random.randint(30,70); d=random.randint(12,30); a=100-h-d
    tip="HOME WIN" if h>55 else "AWAY WIN" if a>38 else "DRAW"
    return {"home":h,"draw":d,"away":a,"tip":f"{tip} {max(h,d,a)}%","over15":random.randint(60,92),"btts":random.randint(38,76)}

@app.route("/")
def home():
    cats={}
    for l in WORLD:
        cats.setdefault(l["c"],[]).append(l)
    return render_template("index.html", cats=cats, leagues=WORLD, now=datetime.now().strftime("%d %b %Y"))

@app.route("/league/<lid>")
def league_page(lid):
    lg=find_league(lid)
    if not lg: return "Not found",404
    return render_template("league.html", lg=lg)

@app.route("/game/<lid>/<int:gid>")
def game_page(lid,gid):
    lg=find_league(lid)
    if not lg or gid>=len(lg["games"]): return "Not found",404
    game=lg["games"][gid]
    pred=predict_for(game)
    return render_template("game.html", lg=lg, game=game, pred=pred)

@app.route("/api/world")
def api():
    return jsonify(WORLD)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
