from flask import Flask, render_template
import os, random

app = Flask(__name__)

def mg(n, teams):
    g=[]
    for i in range(n):
        h,a=random.sample(teams,2)
        t=f"{random.randint(8,21)}:{random.choice(['00','15','30','45'])}"
        g.append(f"{h} vs {a} {t}")
    return g

P = {
 "es":["Real Madrid","Barcelona","Atletico","Sevilla"],
 "gr":["Olympiacos","Panathinaikos","AEK","PAOK"],
 "se":["Malmo","AIK","Djurgarden","Hacken"],
 "en":["Arsenal","Man City","Liverpool","Chelsea"],
 "de":["Bayern","Dortmund","Leverkusen","Leipzig"],
 "fr":["PSG","Marseille","Lyon","Monaco"],
}

UEFA_55 = ["Albania","Andorra","Armenia","Austria","Azerbaijan","Belarus","Belgium","Bosnia and Herzegovina","Bulgaria","Croatia","Cyprus","Czech Republic","Denmark","England","Estonia","Faroe Islands","Finland","France","Georgia","Germany","Gibraltar","Greece","Hungary","Iceland","Israel","Italy","Kazakhstan","Kosovo","Latvia","Liechtenstein","Lithuania","Luxembourg","Malta","Moldova","Montenegro","Netherlands","North Macedonia","Northern Ireland","Norway","Poland","Portugal","Republic of Ireland","Romania","Russia","San Marino","Scotland","Serbia","Slovakia","Slovenia","Spain","Sweden","Switzerland","Turkey","Ukraine","Wales"]

def gen_clubs(c,n=10): return [f"{c} FC {i}" for i in range(1,n+1)]

COUNTRIES={}
for c in UEFA_55:
    if c in ["Spain","Greece","Sweden","England","Germany","France"]: continue
    clubs=gen_clubs(c,10)
    COUNTRIES[c]=[
     {"id":f"{c.lower()}_1","n":f"{c} - Premier (1st)","type":"PRO","games":mg(8,clubs)},
     {"id":f"{c.lower()}_cup","n":f"{c} - Cup (Cup)","type":"CUP","games":mg(6,clubs)},
    ]

COUNTRIES["Spain"]=[{"id":"es_laliga","n":"Spain - LaLiga (1st)","type":"PRO","games":mg(10,P["es"])}]
COUNTRIES["Greece"]=[{"id":"gr_sl","n":"Greece - Super League (1st)","type":"PRO","games":mg(8,P["gr"])}]
COUNTRIES["Sweden"]=[{"id":"se_all","n":"Sweden - Allsvenskan (1st)","type":"PRO","games":mg(8,P["se"])}]
COUNTRIES["England"]=[{"id":"en_pl","n":"England - Premier League (1st)","type":"PRO","games":mg(10,P["en"])}]
COUNTRIES["Germany"]=[{"id":"de_bun","n":"Germany - Bundesliga (1st)","type":"PRO","games":mg(9,P["de"])}]
COUNTRIES["France"]=[{"id":"fr_l1","n":"France - Ligue 1 (1st)","type":"PRO","games":mg(9,P["fr"])}]
COUNTRIES["Botswana"]=[{"id":"bw_prem","n":"Botswana - Premier (1st)","type":"PRO","games":mg(8,["Gaborone Utd","Jwaneng Galaxy","Rollers"])}]

def find_league(lid):
    for country, leagues in COUNTRIES.items():
        for l in leagues:
            if l["id"]==lid:
                l2=l.copy(); l2["country"]=country; return l2
    return None

@app.route("/")
def home(): return render_template("index.html", countries=COUNTRIES)

@app.route("/league/<lid>")
def league_page(lid):
    lg=find_league(lid)
    return render_template("league.html", lg=lg) if lg else ("Not found",404)

@app.route("/game/<lid>/<int:gid>")
def game_page(lid,gid):
    lg=find_league(lid)
    if not lg or gid>=len(lg["games"]): return "Not found",404
    return render_template("game.html", lg=lg, game=lg["games"][gid], gid=gid)

@app.route("/filters")
def filters_page():
    presets=[
        {"cat":"Probability","icon":"🏠","title":"Home Bankers","desc":"The model likes the home side, they win at this ground, and they are on a run.","f":[["MODEL","Home Win","70%+"],["MODEL","League Predictability","Good"],["HOME","Win % home","55%+"],["HOME","Win % last 5 - home","60%+"]],"c":"35 matches in the next 24 hours"},
        {"cat":"Probability","icon":"🎯","title":"BTTS & Win","desc":"The model has the home side winning and both teams scoring.","f":[["MODEL","Home Win","55%+"],["MODEL","BTTS","55%+"],["HOME","Scored +0.5 % home","80%+"],["AWAY","Scored +0.5 % last 6 - away","65%+"]],"c":"64 matches in the next 24 hours"},
        {"cat":"Probability","icon":"✈️","title":"Away Edge","desc":"Travelling sides the model rates above the home team.","f":[["MODEL","Away Win","50%+"],["MODEL","Home Win","Under 30%"],["AWAY","Win % last 10 - away","40%+"],["HOME","Win % last 5 - home","Under 45%"]],"c":"74 matches in the next 24 hours"},
        {"cat":"Probability","icon":"⚽","title":"Goal Rush","desc":"The model wants overs and BTTS, and both sides have been in high-scoring games.","f":[["MODEL","+2.5 Goals","62%+"],["MODEL","BTTS","55%+"],["HOME","+2.5 Goals % last 10","60%+"],["AWAY","BTTS % last 6","55%+"]],"c":"173 matches in the next 24 hours"},
        {"cat":"Probability","icon":"🛡️","title":"Tight Games","desc":"The model expects two goals or fewer, and neither side has been in open games.","f":[["MODEL","-2.5 Goals","62%+"],["MODEL","BTTS","Under 42%"],["HOME","+2.5 Goals %","Under 48%"],["AWAY","+2.5 Goals % last 10","Under 45%"]],"c":"29 matches in the next 24 hours"},
        {"cat":"Probability","icon":"🚩","title":"Corner Kings","desc":"Both teams average high corners, model predicts 9.5+","f":[["MODEL","Over 9.5 Corners","72%+"],["HOME","Corners PG","6.0+"],["AWAY","Corners PG","5.5+"]],"c":"41 matches in the next 24 hours"},
        {"cat":"Value","icon":"💰","title":"Home Value","desc":"Home win prices of 1.90-3.20 that are longer than our model.","f":[["ODDS
