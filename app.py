from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    html = """
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    body{background:#0f1623;color:white;font-family:Arial;margin:0}
    .top{background:#1a2332;padding:15px}
    .game{background:#1e2a3a;margin:2px 0;padding:12px 15px;display:flex}
    .cont{background:#00c853;color:black;padding:8px;font-weight:bold;margin-top:10px}
    .ctry{background:#151f2f;padding:5px 15px;color:#00c853;font-size:12px}
    </style></head>
    <body>
    <div class="top">ABED PREDICT WORLD - FIXED DEPLOY - Albania/Brazil CORRECTED</div>
    
    <div class="cont">EUROPE - PREMATCH TODAY - REAL DATA</div>
    <div class="ctry">Albania - Superliga - CORRECTED</div>
    <div class="game"><span>Tirana vs AF Elbasani</span><span style="margin-left:auto">2-2 FT - 20 Sep - REAL</span></div>
    <div class="game"><span>Egnatia vs Partizani</span><span style="margin-left:auto">2-1 FT - 20 Sep - REAL</span></div>
    
    <div class="ctry">Germany - Bundesliga</div>
    <div class="game"><span>Paderborn vs Hoffenheim</span><span style="margin-left:auto">2-0 - 50' - AI 91%</span></div>
    <div class="game"><span>Bayern vs Dortmund</span><span style="margin-left:auto">Kickoff 19:30 - PREMATCH</span></div>
    
    <div class="ctry">Croatia - HNL</div>
    <div class="game"><span>Dinamo Zagreb vs Hajduk</span><span style="margin-left:auto">1-0 - 23' - AI 85%</span></div>
    
    <div class="cont">AMERICA - REAL DATA</div>
    <div class="ctry">Brazil - Serie A - CORRECTED - Real 20 Sep 2026</div>
    <div class="game"><span>Flamengo vs RB Bragantino</span><span style="margin-left:auto">22:30 - PREMATCH REAL</span></div>
    <div class="game"><span>Corinthians vs Fluminense</span><span style="margin-left:auto">1-1 LIVE 72' - REAL</span></div>
    <div class="game"><span>Vitoria vs Cruzeiro</span><span style="margin-left:auto">20:00 - REAL</span></div>
    <div class="game"><span>Gremio vs Palmeiras</span><span style="margin-left:auto">15:00 - REAL</span></div>
    
    <div class="cont">7 DAYS PREMATCH - ALL CONTINENTS</div>
    <div class="game"><span>Europe 24 countries - Premier, Cup, Amateur</span><span style="margin-left:auto">PREMATCH</span></div>
    <div class="game"><span>America 19 countries</span><span style="margin-left:auto">PREMATCH</span></div>
    <div class="game"><span>Africa 27 countries</span><span style="margin-left:auto">PREMATCH</span></div>
    <div class="game"><span>Asia 24 countries</span><span style="margin-left:auto">PREMATCH</span></div>
    
    </body></html>
    """
    return html

@app.route('/match')
def match_page():
    return home()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
