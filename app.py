from flask import Flask, render_template, jsonify
import os, random
app = Flask(__name__)

def mg(n, teams):
    g=[]
    for i in range(n):
        h,a=random.sample(teams,2)
        t=f"{random.randint(8,21)}:{random.choice(['00','15','30','45'])}"
        g.append(f"{h} vs {a} {t}")
    return g

# TEAM POOLS
P={
"es":["Real Madrid","Barcelona","Atletico","Sevilla","Valencia","Villarreal","Betis","Bilbao"],
"gr":["Olympiacos","Panathinaikos","AEK","PAOK","Aris","Volos"],
"se":["Malmo","AIK","Djurgarden","Hacken","Hammarby","Elfsborg"],
"en":["Arsenal","Man City","Liverpool","Chelsea","Man Utd","Tottenham"],
"de":["Bayern","Dortmund","Leverkusen","Leipzig","Stuttgart","Frankfurt"],
"it":["Inter","Milan","Napoli","Juventus","Roma","Lazio"],
"fr":["PSG","Marseille","Lyon","Monaco","Lille","Nice"],
}

UEFA_55=[
"Albania","Andorra","Armenia","Austria","Azerbaijan","Belarus","Belgium","Bosnia and Herzegovina",
"Bulgaria","Croatia","Cyprus","Czech Republic","Denmark","England","Estonia","Faroe Islands","Finland",
"France","Georgia","Germany","Gibraltar","Greece","Hungary","Iceland","Israel","Italy","Kazakhstan",
"Kosovo","Latvia","Liechtenstein","Lithuania","Luxembourg","Malta","Moldova","Montenegro","Netherlands",
"North Macedonia","Northern Ireland","Norway","Poland","Portugal","Republic of Ireland","Romania","Russia",
"San Marino","Scotland","Serbia","Slovakia","Slovenia","Spain","Sweden","Switzerland","Turkey","Ukraine","Wales"
]

# HELPER to create fake club names for auto countries
def gen_clubs(country, n=12):
    base=[f"{country} FC {i}" for i in range(1,4)]+ [f"{country} United",f"{country} City",f"{country} SC",f"FK {country}",f"FC {country}"]
    # mix with generic
    while len(base)<n:
        base.append(f"{country} Club {len(base)+1}")
    return base[:n]

COUNTRIES={}

# 1. BUILD ALL UEFA AUTOMATICALLY
for country in UEFA_55:
    # skip if we will override with detailed later
    if country in ["Spain","Greece","Sweden","England","Germany","Italy","France"]:
        continue
    clubs=gen_clubs(country, 12)
    clubs2=gen_clubs(country+" 2", 10)
    clubsAm=gen_clubs(country+" Am", 14)
    COUNTRIES[country]=[
     {"id":f"{country.lower().replace(' ','_')}_1","n":f"{country} - Premier / Super League (1st)","type":"PRO","games":mg(10,clubs)},
     {"id":f"{country.lower().replace(' ','_')}_2","n":f"{country} - 2nd Division","type":"PRO 2","games":mg(10,clubs2)},
     {"id":f"{country.lower().replace(' ','_')}_3","n":f"{country} - 3rd Division / Amateur","type":"AMATEUR","games":mg(12,clubsAm)},
     {"id":f"{country.lower().replace(' ','_')}_4","n":f"{country} - 4th Division / Regional Amateur","type":"AMATEUR","games":mg(14,clubsAm)},
     {"id":f"{country.lower().replace(' ','_')}_cup","n":f"{country} - National Cup (Cup)","type":"CUP","games":mg(8,clubs+clubs2)},
     {"id":f"{country.lower().replace(' ','_')}_supercup","n":f"{country} - Super Cup / League Cup (Cup)","type":"CUP","games":mg(4,clubs)},
    ]

# 2. OVERRIDE WITH DETAILED FOR YOUR FAVORITE 7
COUNTRIES["Spain"]=[
 {"id":"es_laliga","n":"Spain - LaLiga (1st)","type":"PRO","games":mg(10,P["es"])},
 {"id":"es_laliga2","n":"Spain - LaLiga 2 (2nd)","type":"PRO 2","games":mg(11,["Granada","Leganes","Eibar","Almeria","Valladolid","Espanyol"])},
 {"id":"es_rfef","n":"Spain - Primera RFEF (Amateur / 3rd)","type":"AMATEUR","games":mg(14,["Betis B","Sevilla At","Alcoyano","Marbella","Ibiza","Antequera"])},
 {"id":"es_rfef2","n":"Spain - Segunda RFEF (Amateur / 4th)","type":"AMATEUR","games":mg(16,["Atletico B","Castilla","Alcorcon","Merida"])},
 {"id":"es_copa","n":"Spain - Copa del Rey (Cup)","type":"CUP","games":mg(12,P["es"])},
 {"id":"es_supercopa","n":"Spain - Supercopa (Cup)","type":"CUP","games":mg(4,P["es"])},
]
COUNTRIES["Greece"]=[
 {"id":"gr_sl","n":"Greece - Super League (1st)","type":"PRO","games":mg(8,P["gr"])},
 {"id":"gr_sl2","n":"Greece - Super League 2 (2nd)","type":"PRO 2","games":mg(10,["Larissa","Kallithea","Levadiakos","Kalamata"])},
 {"id":"gr_gam","n":"Greece - Gamma Ethniki (Amateur / 3rd)","type":"AMATEUR","games":mg(12,["Ethnikos","Diagoras","Ilioupoli","Giouchtas"])},
 {"id":"gr_cup","n":"Greece - Cup (Cup)","type":"CUP","games":mg(8,P["gr"])},
]
COUNTRIES["Sweden"]=[
 {"id":"se_all","n":"Sweden - Allsvenskan (1st)","type":"PRO","games":mg(8,P["se"])},
 {"id":"se_super","n":"Sweden - Superettan (2nd)","type":"PRO 2","games":mg(10,["Osters","GAIS","Orebro","Vasteras","Helsingborg"])},
 {"id":"se_ettan","n":"Sweden - Ettan (Amateur / 3rd)","type":"AMATEUR","games":mg(12,["Trollhattan","Falkenberg","Ljungskile","Sollentuna"])},
 {"id":"se_div2","n":"Sweden - Division 2 (Amateur / 4th)","type":"AMATEUR","games":mg(14,["IFK Lulea","Husqvarna","Nordic Utd"])},
 {"id":"se_cup","n":"Sweden - Svenska Cupen (Cup)","type":"CUP","games":mg(8,P["se"])},
]
COUNTRIES["England"]=[
 {"id":"en_pl","n":"England - Premier League (1st)","type":"PRO","games":mg(10,P["en"])},
 {"id":"en_ch","n":"England - Championship (2nd)","type":"PRO 2","games":mg(12,["Leeds","Leicester","Southampton","Ipswich","Middlesbrough"])},
 {"id":"en_l1","n":"England - League One (3rd)","type":"PRO 3","games":mg(12,["Barnsley","Derby","Bolton","Portsmouth"])},
 {"id":"en_l2","n":"England - League Two (4th)","type":"PRO 4","games":mg(12,["Bradford","Wrexham","Notts Co","Stockport"])},
 {"id":"en_nat","n":"England - National League (Amateur / 5th)","type":"AMATEUR","games":mg(12,["Chesterfield","Barnet","Oldham","York"])},
 {"id":"en_nat2","n":"England - National North/South (Amateur / 6th)","type":"AMATEUR","games":mg(14,["Brackley","Hemel","Farsley","Bath"])},
 {"id":"en_fa","n":"England - FA Cup (Cup)","type":"CUP","games":mg(14,P["en"])},
 {"id":"en_eflcup","n":"England - Carabao Cup (Cup)","type":"CUP","games":mg(10,P["en"])},
]
COUNTRIES["Germany"]=[
 {"id":"de_bun","n":"Germany - Bundesliga (1st)","type":"PRO","games":mg(9,P["de"])},
 {"id":"de_bun2","n":"Germany - 2. Bundesliga (2nd)","type":"PRO 2","games":mg(9,["Hamburg","Schalke","Hertha","Kaiserslautern","Hannover"])},
 {"id":"de_3liga","n":"Germany - 3. Liga (3rd)","type":"PRO 3","games":mg(10,["Aachen","Wuppertal","Chemnitzer","Offenbach"])},
 {"id":"de_reg","n":"Germany - Regionalliga (Amateur / 4th)","type":"AMATEUR","games":mg(14,["Bayern II","Dortmund II","Viktoria Berlin"])},
 {"id":"de_ober","n":"Germany - Oberliga (Amateur / 5th)","type":"AMATEUR","games":mg(16,["Chemie Leipzig","Babelsberg","Kiel II"])},
 {"id":"de_pokal","n":"Germany - DFB-Pokal (Cup)","type":"CUP","games":mg(10,P["de"])},
]
COUNTRIES["Italy"]=[
 {"id":"it_a","n":"Italy - Serie A (1st)","type":"PRO","games":mg(10,P["it"])},
 {"id":"it_b","n":"Italy - Serie B (2nd)","type":"PRO 2","games":mg(10,["Sampdoria","Palermo","Parma","Como","Venezia"])},
 {"id":"it_c","n":"Italy - Serie C (Amateur / 3rd)","type":"AMATEUR","games":mg(12,["Juventus U23","Catania","Benevento","Crotone"])},
 {"id":"it_d","n":"Italy - Serie D (Amateur / 4th)","type":"AMATEUR","games":mg(14,["Sambenedettese","Pistoiese","Grosseto"])},
 {"id":"it_coppa","n":"Italy - Coppa Italia (Cup)","type":"CUP","games":mg(10,P["it"])},
]
COUNTRIES["France"]=[
 {"id":"fr_l1","n":"France - Ligue 1 (1st)","type":"PRO","games":mg(9,P["fr"])},
 {"id":"fr_l2","n":"France - Ligue 2 (2nd)","type":"PRO 2","games":mg(9,["Bordeaux","Saint-Etienne","Angers","Auxerre"])},
 {"id":"fr_nat","n":"France - National (Amateur / 3rd)","type":"AMATEUR","games":mg(10,["Versailles","Red Star","Concarneau","Martigues"])},
 {"id":"fr_nat2","n":"France - National 2 (Amateur / 4th)","type":"AMATEUR","games":mg(12,["Beauvais","Les Herbiers","Andrezieux"])},
 {"id":"fr_coupe","n":"France - Coupe de France (Cup)","type":"CUP","games":mg(10,P["fr"])},
]

# ADD NON-UEFA YOU ALREADY HAD
COUNTRIES["Botswana"]=[
 {"id":"bw_prem","n":"Botswana - Premier (1st)","type":"PRO","games":mg(8,["Gaborone Utd","Jwaneng Galaxy","Rollers","Orapa Utd","BDF XI","Masitaoka"])},
 {"id":"bw_first","n":"Botswana - First Division (Amateur / 2nd)","type":"AMATEUR","games":mg(12,["BMC","Extension Gunners","Black Forest","Centre Chiefs","Tlokweng Utd"])},
 {"id":"bw_fa","n":"Botswana - FA Cup (Cup)","type":"CUP","games":mg(8,["Gaborone Utd","Rollers","Galaxy","Police XI"])},
]
COUNTRIES["South Africa"]=[
 {"id":"za_psl","n":"South Africa - PSL (1st)","type":"PRO","games":mg(8,["Sundowns","Chiefs","Pirates","SuperSport","CT City","Stellenbosch"])},
 {"id":"za_chal","n":"South Africa - Motsepe (2nd)","type":"PRO 2","games":mg(10,["Orbit College","Pretoria Callies","Hungry Lions","Upington"])},
 {"id":"za_abc","n":"South Africa - ABC Motsepe (Amateur / 3rd)","type":"AMATEUR","games":mg(14,["Highlands Park","La Masia","Milford"])},
 {"id":"za_ned","n":"South Africa - Nedbank Cup (Cup)","type":"CUP","games":mg(8,["Sundowns","Chiefs","Pirates"])},
]
COUNTRIES["UEFA Cups (All Europe)"]=[
 {"id":"ucl","n":"UEFA Champions League (Cup Europe)","type":"CUP","games":mg(16,["Real Madrid","Man City","Bayern","Inter","PSG","Arsenal","Barcelona"])},
 {"id":"uel","n":"UEFA Europa League (Cup Europe)","type":"CUP","games":mg(16,["Liverpool","Roma","Leverkusen","Marseille","Benfica","Ajax"])},
 {"id":"uecl","n":"UEFA Conference League (Cup Europe)","type":"CUP","games":mg(16,["Fiorentina","Aston Villa","Lille","Fenerbahce","PAOK"])},
]

def find_league(lid):
    for country, leagues in COUNTRIES.items():
        for l in leagues:
            if l["id"]==lid:
                l2=l.copy(); l2["country"]=country
                return l2
    return None

def predict_for(game):
    random.seed(hash(game)%100000)
    h=random.randint(30,70); d=random.randint(12,30); a=100-h-d
    tip="HOME WIN" if h>55 else "AWAY WIN" if a>38 else "DRAW"
    return {"home":h,"draw":d,"away":a,"tip":f"{tip} {max(h,d,a)}%","over15":random.randint(60,92),"btts":random.randint(38,76)}

@app.route("/")
def home():
    return render_template("index.html", countries=COUNTRIES)

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
    return jsonify({k: len(v) for k,v in COUNTRIES.items()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
