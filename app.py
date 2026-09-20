from flask import Flask, render_template, jsonify
import os
from datetime import datetime
app = Flask(__name__)

WORLD = [
  {"id":"africa","n":"Africa","f":12,"games":["Mamelodi Sundowns vs Al Ahly 15:00","Simba vs Wydad 18:00","Pyramids vs Esperance 21:00"]},
  {"id":"albania","n":"Albania","f":2,"games":["Tirana vs Partizani 16:00","Vllaznia vs Egnatia 19:00"]},
  {"id":"germany","n":"Germany - Bundesliga","f":9,"hl":"LIVE","games":["Leverkusen vs RB Leipzig 14:30 LIVE 2-1","Bayern vs Dortmund 16:30","Stuttgart vs Frankfurt 16:30"]},
  {"id":"england","n":"England - Premier League","f":10,"games":["Arsenal vs Man City 14:00","Liverpool vs Chelsea 16:30","Man Utd vs Tottenham 18:45"]},
  {"id":"spain","n":"Spain - LaLiga","f":8,"games":["Real Madrid vs Barcelona 20:00","Atletico vs Sevilla 18:00"]},
  {"id":"italy","n":"Italy - Serie A","f":7,"games":["Inter vs Milan 19:45","Napoli vs Juventus 17:00"]},
  {"id":"france","n":"France - Ligue 1","f":6,"games":["PSG vs Marseille 20:45"]},
  {"id":"asia","n":"Asia","f":15,"games":["Al Nassr vs Al Hilal 19:00"]},
]

def find_league(lid):
    for l in WORLD:
        if l["id"]==lid:
            return l
    return None

@app.route("/")
def home():
    return render_template("index.html", leagues=WORLD, now=datetime.now().strftime("%d %b %Y"))

@app.route("/league/<lid>")
def league_page(lid):
    lg=find_league(lid)
    if not lg:
        return "Not found",404
    return render_template("league.html", lg=lg, now=datetime.now().strftime("%d %b %Y"))

@app.route("/api/world")
def api():
    return jsonify(WORLD)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
