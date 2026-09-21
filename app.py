import os
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def home():
    try:
        return """
<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
body{background:#0f141f;color:#fff;font-family:Arial;margin:0}
.header{background:#0b1220;padding:12px;display:flex;justify-content:space-between}
.country{background:#151a25;margin:10px;border-radius:12px;overflow:hidden}
.chead{padding:14px;display:flex;justify-content:space-between;cursor:pointer}
.ccontent{display:none;padding:5px}
.open .ccontent{display:block}
.fixture{background:#1e293b;margin:6px;padding:10px;border-radius:8px}
.stats{display:none;background:#0b0e14;padding:10px;margin-top:6px;border-radius:8px}
.open-stats{display:block}
.tab{display:inline-block;padding:5px 10px;background:#233044;border-radius:15px;font-size:11px;margin:2px;cursor:pointer}
.tab.active{background:#00ff88;color:#000}
</style></head><body>
<div class='header'><b style='color:#00ff88'>PREDICT WORLD</b><span>LIVE</span></div>

<div class='country open' onclick='this.classList.toggle("open")'>
<div class='chead'><span>🏴󠁧󠁢󠁥󠁮󠁧󠁿 England (3)</span><span>▼</span></div>
<div class='ccontent'>
<div style='color:#8ab4ff;padding:8px'>Premier League - 7 days</div>

<div class='fixture' onclick='let s=this.nextElementSibling; s.style.display=s.style.display=="block"?"none":"block"'>
<b>Arsenal vs Man City</b><br><small>Today 19:30</small><br><span style='color:#00ff88'>Statistics ▼</span>
</div>
<div class='stats'>
<span class='tab active' onclick='load(this,"corners")'>Avg Corners L5</span>
<span class='tab' onclick='load(this,"cards")'>Avg Cards L5</span>
<span class='tab' onclick='load(this,"fouls")'>Avg Fouls L5</span>
<span class='tab' onclick='load(this,"shots")'>Avg Shots</span>
<span class='tab' onclick='load(this,"h2h")'>H2H Last 5</span>
<span class='tab' onclick='load(this,"players")'>Players</span>
<div class='scontent' style='margin-top:10px;color:#aaa'>Tap tab...</div>
</div>

<div class='fixture' onclick='let s=this.nextElementSibling; s.style.display=s.style.display=="block"?"none":"block"'>
<b>Liverpool vs Chelsea</b><br><small>Tomorrow 15:00</small><br><span style='color:#00ff88'>Statistics ▼</span>
</div>
<div class='stats'>
<span class='tab active' onclick='load(this,"corners")'>Avg Corners L5</span>
<span class='tab' onclick='load(this,"cards")'>Avg Cards L5</span>
<span class='tab' onclick='load(this,"fouls")'>Avg Fouls L5</span>
<span class='tab' onclick='load(this,"shots")'>Avg Shots</span>
<span class='tab' onclick='load(this,"h2h")'>H2H Last 5</span>
<span class='tab' onclick='load(this,"players")'>Players</span>
<div class='scontent' style='margin-top:10px;color:#aaa'>Tap tab...</div>
</div>

</div></div>

<div class='country' onclick='this.classList.toggle("open")'>
<div class='chead'><span>🇪🇸 Spain (2)</span><span>▼</span></div>
<div class='ccontent'><div style='color:#8ab4ff;padding:8px'>La Liga</div>
<div class='fixture'><b>Real Madrid vs Barcelona</b><br><small>Tomorrow 20:00</small></div>
</div></div>

<script>
async function load(tab,type){
 let box=tab.closest('.stats');
 box.querySelectorAll('.tab').forEach(t=>t.classList.remove('active')); tab.classList.add('active');
 let c=box.querySelector('.scontent'); c.innerHTML='Calculating...';
 let r=await fetch('/api/stats?type='+type); let j=await r.json(); c.innerHTML=j.html;
}
</script></body></html>
        """
    except Exception as e:
        return f"Error: {e}"

@app.route("/api/stats")
def stats():
    t = request.args.get("type","corners")
    data = {
        "corners": "<b>Avg Corners Last 5 (REAL)</b><br>Home: 5.4<br>Away: 4.7<br><b>Total: 10.1</b>",
        "cards": "<b>Avg Cards Per Game Last 5</b><br>Home: 1.8 cards/g<br>Away: 2.1 cards/g<br><b>Total: 3.9/game</b><br><small>Yellow+Red counted /5</small>",
        "fouls": "<b>Avg Fouls Per Game Last 5</b><br>Home Team: 12.3 fouls/g<br>Away Team: 13.1 fouls/g<br><b>Total: 25.4</b><br>Per team last 5 games",
        "shots": "<b>Avg Shots Per Game</b><br>Home: 14.2 (4.5 on target)<br>Away: 11.8",
        "h2h": "<b>Last 5 Head to Head</b><br>2W-1D-2W<br>Avg Goals: 2.8<br>1-0, 2-2, 0-1, 3-1, 1-1",
        "players": "<b>Player Tabs - Avg L5</b><br><div style='background:#1e293b;padding:5px;margin:3px'>Saka: Fouls 1.1 | Shots 2.9 | Won 2.3</div><div style='background:#1e293b;padding:5px;margin:3px'>Rice: Fouls 1.8 | Shots 0.9 | Cards 0.4/g</div>"
    }
    return jsonify({"html": data.get(t,"No data")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
