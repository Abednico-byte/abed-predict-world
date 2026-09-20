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

P={
"es":["Real Madrid","Barcelona","Atletico","Sevilla","Valencia","Villarreal","Betis","Bilbao","Sociedad","Girona"],
"es2":["Granada","Leganes","Eibar","Almeria","Valladolid","Espanyol","Oviedo","Zaragoza"],
"es3":["Betis B","Sevilla At","Alcoyano","Marbella","Ibiza","Antequera","Merida","Alcorcon","Atletico B","Castilla"],
"gr":["Olympiacos","Panathinaikos","AEK","PAOK","Aris","Volos","Atromitos","Asteras"],
"gr2":["Larissa","Kallithea","Levadiakos","Kalamata","Ionikos","Chania","Kifisia"],
"se":["Malmo","AIK","Djurgarden","Hacken","Hammarby","Elfsborg","Goteborg","Norrkoping"],
"se2":["Osters","GAIS","Orebro","Vasteras","Helsingborg","Brage","Utsikten","Gefle"],
"se3":["Trollhattan","Falkenberg","Ljungskile","Sollentuna","Lulea","Husqvarna","Nordic Utd","Angelholm"],
"en":["Arsenal","Man City","Liverpool","Chelsea","Man Utd","Tottenham","Newcastle","Villa"],
"en2":["Leeds","Leicester","Southampton","Ipswich","West Brom","Boro","Norwich","Coventry"],
"en3":["Barnsley","Derby","Bolton","Portsmouth","Reading","Charlton"],
"en4":["Wrexham","Notts Co","Chesterfield","Barnet","Oldham","York","Bromley","Hartlepool"],
"de":["Bayern","Dortmund","Leverkusen","Leipzig","Stuttgart","Frankfurt","Wolfsburg","Union"],
"de2":["Hamburg","Schalke","Hertha","Kaiserslautern","Nurnberg","Hannover","Paderborn"],
"de3":["Aachen","Wuppertal","Chemnitzer","Offenbach","Bayern II","Dortmund II","Viktoria Berlin"],
"it":["Inter","Milan","Napoli","Juventus","Roma","Lazio","Atalanta","Fiorentina"],
"it2":["Sampdoria","Palermo","Parma","Como","Venezia","Cremonese"],
"it3":["Juventus U23","Catania","Benevento","Crotone","Perugia","Triestina"],
"fr":["PSG","Marseille","Lyon","Monaco","Lille","Nice","Rennes","Lens"],
"us":["Inter Miami","LAFC","LA Galaxy","Columbus","Atlanta","NYCFC","Seattle","Cincinnati"],
"us2":["Indy Eleven","Sacramento","Louisville","Detroit","Charleston","Phoenix"],
"mx":["America","Chivas","Cruz Azul","Pumas","Tigres","Monterrey","Atlas","Santos"],
"br":["Flamengo","Palmeiras","Corinthians","Santos","Sao Paulo","Fluminense","Botafogo","Gremio"],
"ar":["River Plate","Boca Juniors","Racing","Independiente","San Lorenzo","Rosario"],
"bw":["Gaborone Utd","Jwaneng Galaxy","Rollers","Orapa Utd","BDF XI","Masitaoka","Morupule","Police XI"],
"bw2":["BMC","Extension Gunners","Black Forest","Mogoditshane","Centre Chiefs","Tlokweng Utd","Holy Ghost","VTM"],
"za":["Sundowns","Chiefs","Pirates","SuperSport","CT City","Stellenbosch","AmaZulu","Sekhukhune"],
"za2":["Orbit College","Pretoria Callies","Hungry Lions","Upington","Milford","Baroka","La Masia"],
"eg":["Al Ahly","Zamalek","Pyramids","Al Masry","Future","ENPPI","Ceramica"],
"jp":["Urawa","Kawasaki","Yokohama FM","Vissel Kobe","Kashima","Gamba Osaka"],
"sa":["Al Nassr","Al Hilal","Al Ittihad","Al Ahli","Al Ettifaq","Al Shabab"],
}

COUNTRIES={
"Spain": [
 {"id":"es_laliga","n":"LaLiga (1st)","type":"PRO","games":mg(10,P["es"])},
 {"id":"es_laliga2","n":"LaLiga 2 (2nd)","type":"PRO 2","games":mg(11,P["es2"])},
 {"id":"es_rfef","n":"Primera RFEF - Group 1 & 2 (Amateur / 3rd)","type":"AMATEUR","games":mg(14,P["es3"])},
 {"id":"es_rfef2","n":"Segunda RFEF (Amateur / 4th)","type":"AMATEUR","games":mg(16,P["es3"])},
 {"id":"es_copa","n":"Copa del Rey (Cup)","type":"CUP","games":mg(12,P["es"]+P["es2"])},
 {"id":"es_supercopa","n":"Supercopa de España (Cup)","type":"CUP","games":mg(4,P["es"])},
],
"Greece": [
 {"id":"gr_sl","n":"Super League (1st)","type":"PRO","games":mg(8,P["gr"])},
 {"id":"gr_sl2","n":"Super League 2 (2nd)","type":"PRO 2","games":mg(10,P["gr2"])},
 {"id":"gr_gam","n":"Gamma Ethniki (Amateur / 3rd)","type":"AMATEUR","games":mg(12,P["gr2"])},
 {"id":"gr_cup","n":"Greek Cup (Cup)","type":"CUP","games":mg(8,P["gr"])},
],
"Sweden": [
 {"id":"se_all","n":"Allsvenskan (1st)","type":"PRO","games":mg(8,P["se"])},
 {"id":"se_super","n":"Superettan (2nd)","type":"PRO 2","games":mg(10,P["se2"])},
 {"id":"se_ettan","n":"Ettan Norra & Sodra (Amateur / 3rd)","type":"AMATEUR","games":mg(12,P["se3"])},
 {"id":"se_div2","n":"Division 2 (Amateur / 4th)","type":"AMATEUR","games":mg(14,P["se3"])},
 {"id":"se_cup","n":"Svenska Cupen (Cup)","type":"CUP","games":mg(8,P["se"]+P["se2"])},
],
"England": [
 {"id":"en_pl","n":"Premier League (1st)","type":"PRO","games":mg(10,P["en"])},
 {"id":"en_ch","n":"Championship (2nd)","type":"PRO 2","games":mg(12,P["en2"])},
 {"id":"en_l1","n":"League One (3rd)","type":"PRO 3","games":mg(12,P["en3"])},
 {"id":"en_l2","n":"League Two (4th)","type":"PRO 4","games":mg(12,P["en3"])},
 {"id":"en_nat","n":"National League (Amateur / 5th)","type":"AMATEUR","games":mg(12,P["en4"])},
 {"id":"en_nat_n","n":"National North/South (Amateur / 6th)","type":"AMATEUR","games":mg(14,P["en4"])},
 {"id":"en_fa","n":"FA Cup (Cup)","type":"CUP","games":mg(14,P["en"]+P["en4"])},
 {"id":"en_eflcup","n":"Carabao Cup (Cup)","type":"CUP","games":mg(10,P["en"]+P["en2"])},
],
"Germany": [
 {"id":"de_bun","n":"Bundesliga (1st)","type":"PRO","games":mg(9,P["de"])},
 {"id":"de_bun2","n":"2. Bundesliga (2nd)","type":"PRO 2","games":mg(9,P["de2"])},
 {"id":"de_3liga","n":"3. Liga (3rd)","type":"PRO 3","games":mg(10,P["de2"])},
 {"id":"de_reg","n":"Regionalliga (Amateur / 4th)","type":"AMATEUR","games":mg(14,P["de3"])},
 {"id":"de_ober","n":"Oberliga (Amateur / 5th)","type":"AMATEUR","games":mg(16,P["de3"])},
 {"id":"de_pokal","n":"DFB-Pokal (Cup)","type":"CUP","games":mg(10,P["de"]+P["de2"])},
],
"USA": [
 {"id":"us_mls","n":"MLS (1st)","type":"PRO","games":mg(14,P["us"])},
 {"id":"us_usl","n":"USL Championship (2nd)","type":"PRO 2","games":mg(12,P["us2"])},
 {"id":"us_usl1","n":"USL League One (Amateur / 3rd)","type":"AMATEUR","games":mg(10,P["us2"])},
 {"id":"us_open","n":"US Open Cup (Cup)","type":"CUP","games":mg(10,P["us"])},
 {"id":"us_leaguescup","n":"Leagues Cup (Cup)","type":"CUP","games":mg(8,P["us"]+P["mx"])},
],
"Mexico": [
 {"id":"mx_liga","n":"Liga MX (1st)","type":"PRO","games":mg(9,P["mx"])},
 {"id":"mx_exp","n":"Liga de Expansión (2nd)","type":"PRO 2","games":mg(10,["Cancun","Celaya","Leones Negros","Tapatío","Atlante"])},
 {"id":"mx_cup","n":"Copa MX (Cup)","type":"CUP","games":mg(8,P["mx"])},
],
"Botswana": [
 {"id":"bw_prem","n":"Premier League (1st)","type":"PRO","games":mg(8,P["bw"])},
 {"id":"bw_first","n":"First Division North/South (Amateur / 2nd)","type":"AMATEUR","games":mg(12,P["bw2"])},
 {"id":"bw_fa","n":"FA Cup (Cup)","type":"CUP","games":mg(8,P["bw"]+P["bw2"])},
],
"South Africa": [
 {"id":"za_psl","n":"Betway Premiership (1st)","type":"PRO","games":mg(8,P["za"])},
 {"id":"za_chal","n":"Motsepe Championship (2nd)","type":"PRO 2","games":mg(10,P["za2"])},
 {"id":"za_abc","n":"ABC Motsepe League (Amateur / 3rd)","type":"AMATEUR","games":mg(14,P["za2"])},
 {"id":"za_ned","n":"Nedbank Cup (Cup)","type":"CUP","games":mg(8,P["za"]+P["za2"])},
],
"Africa - Other": [
 {"id":"eg_prem","n":"Egypt - Premier (1st)","type":"PRO","games":mg(10,P["eg"])},
 {"id":"ma_bot","n":"Morocco - Botola (1st)","type":"PRO","games":mg(8,["Wydad","Raja","FAR Rabat","RS Berkane"])},
 {"id":"ng_npfl","n":"Nigeria - NPFL (1st)","type":"PRO","games":mg(10,["Enyimba","Rangers","Remo Stars","Kano Pillars"])},
 {"id":"caf_cl","n":"CAF Champions League (Cup Africa)","type":"CUP","games":mg(8,P["eg"])},
 {"id":"caf_conf","n":"CAF Confederation Cup (Cup)","type":"CUP","games":mg(8,P["eg"])},
],
"Asia": [
 {"id":"sa_pro","n":"Saudi Arabia - Pro League","type":"PRO","games":mg(9,P["sa"])},
 {"id":"sa_div1","n":"Saudi Arabia - Division 1 (2nd)","type":"PRO 2","games":mg(10,["Al Qadsiah","Al Orobah","Al Jabalain"])},
 {"id":"jp_j1","n":"Japan - J1 League","type":"PRO","games":mg(10,P["jp"])},
 {"id":"jp_j3","n":"Japan - J3 (Amateur / 3rd)","type":"AMATEUR","games":mg(10,["FC Osaka","Matsumoto","Fukushima"])},
 {"id":"afc_cl","n":"AFC Champions League (Cup Asia)","type":"CUP","games":mg(8,P["sa"]+P["jp"])},
 {"id":"king_cup","n":"Saudi King Cup (Cup)","type":"CUP","games":mg(8,P["sa"])},
],
"Europe - Other & Cups": [
 {"id":"it_a","n":"Italy - Serie A","type":"PRO","games":mg(10,P["it"])},
 {"id":"it_b","n":"Italy - Serie B","type":"PRO 2","games":mg(10,P["it2"])},
 {"id":"it_c","n":"Italy - Serie C (Amateur)","type":"AMATEUR","games":mg(12,P["it3"])},
 {"id":"it_coppa","n":"Italy - Coppa Italia (Cup)","type":"CUP","games":mg(8,P["it"])},
 {"id":"fr_l1","n":"France - Ligue 1","type":"PRO","games":mg(9,P["fr"])},
 {"id":"fr_nat","n":"France - National (Amateur)","type":"AMATEUR","games":mg(10,["Versailles","Red Star","Concarneau","Martigues"])},
 {"id":"fr_coupe","n":"France - Coupe de France (Cup)","type":"CUP","games":mg(10,P["fr"])},
 {"id":"ucl","n":"UEFA Champions League (Cup Europe)","type":"CUP","games":mg(12,P["it"]+P["de"]+P["en"])},
 {"id":"uel","n":"UEFA Europa League (Cup Europe)","type":"CUP","games":mg(12,P["it"]+P["de"]+P["en"])},
],
}

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
    return jsonify(COUNTRIES)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
