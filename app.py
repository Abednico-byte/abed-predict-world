from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime

app = Flask(__name__)

def get_world():
    return [
        {"c":"🌍","n":"Africa","f":12,"l":54},
        {"c":"🇦🇱","n":"Albania","f":2},
        {"c":"🇦🇩","n":"Andorra","f":1},
        {"c":"🇦🇴","n":"Angola","f":3},
        {"c":"🇦🇷","n":"Argentina","f":8,"lg":"Liga Profesional"},
        {"c":"🇦🇲","n":"Armenia"},
        {"c":"🌏","n":"Asia","f":15,"l":120},
        {"c":"🇦🇹","n":"Austria","lg":"Bundesliga"},
        {"c":"🇩🇪","n":"Germany","lg":"Bundesliga","hl":"Bayer Leverkusen vs RB Leipzig 14:30 LIVE","f":9},
        {"c":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","n":"England","lg":"Premier League","f":10},
        {"c":"🇪🇸","n":"Spain","lg":"LaLiga"},
        {"c":"🇮🇹","n":"Italy","lg":"Serie A"},
        {"c":"🇫🇷","n":"France","lg":"Ligue 1"},
    ]

def get_match():
    return {
        "m":"Bayer Leverkusen vs RB Leipzig",
        "d":"20 Sep 2026 14:30 BayArena",
        "avg":3.4,"btts":70,"o25":60,"corn":9.8,
        "pred":{"h":61.9,"d":19.6,"a":18.5,"x":81.5,"o05":96.2,"o15":84.5,"o25":68.3},
        "lev":"Flekken, Medina, Tapsoba, Bade, Vazquez, Garcia, Andrich, Diaby, Schick",
        "rbl":"Vandevoordt, Raum, Lukeba, Orban, Henrichs, Nusa, Gomis",
    }

@app.route("/")
def home():
    return render_template("index.html", leagues=get_world(), match=get_match(), now=datetime.now().strftime("%d %b %Y"), brand="ABED PREDICT")

@app.route("/api/world")
def api_world():
    return jsonify({"leagues":get_world(),"match":get_match(),"brand":"ABED PREDICT"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
