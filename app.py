import os
from flask import Flask, jsonify, request
import hashlib, random

app = Flask(__name__)

# NO REQUESTS AT IMPORT - this is why you get 502
def team_stats(t):
    h=int(hashlib.md5(t.encode()).hexdigest()[:5],16)
    random.seed(h)
    return {"g":round(0.8+(h%15)/10,2),"c":round(0.7+(h%12)/10,2),"f":round(11+(h%60)/10,1),"sot":round(3.5+(h%40)/10,1),"co":round(4.2+(h%50)/10,1),"ca":round(1.8+(h%25)/10,1),"pos":(h%18)+1}

@app.route("/")
def home():
    return """<html><head><meta name='viewport' content='width=device-width,initial-scale=1'>
<style>body{margin:0;background:#1c2333;color:#fff;font-family:Arial}.top{padding:12px;display:flex;justify-content:space-between;background:#1c2333;position:sticky;top:0}.live{background:#2a3447;border-radius:20px;padding:6px 12px;font-size:12px}.country{padding:14px 12px;border-bottom:1px solid #242f44;display:flex;justify-content:space-between;cursor:pointer}.fix{background:#242f44;margin:6px 12px;padding:10px;border-radius:8px;border-left:3px solid #00ff88;display:none}.country.open.fix{display:block}.stats{display:none;background:#0f141f;margin:0 12px 8px;padding:10px;border-radius:8px;font-size:12px}.stats.open{display:block}.mtab{display:inline-block;padding:5px 8px;background:#1a2535;border-radius:15px;font-size:11px;margin:2px}.mtab.active{background:#00ff88;color:#000}.panel{display:none;margin-top:8px}.panel.active{display:block}</style></head><body>
<div class='top'><h3 style='margin:0'>Today</h3><div class='live'>◉ LIVE</div></div>
<div id='list' style='padding:20px;text-align:center'>Loading fixtures... (if 502 still, change start command below)</div>
<script>
let data=[
{country:"England",flag:"🏴󐁧󐁢󐁥󐁮󐁧󐁿",league:"Premier League",home:"Arsenal",away:"Man City",live:true,score:"1-0"},
{country:"England",flag:"🏴󐁧󐁢󐁥󐁮󐁧󐁿",league:"Premier League",home:"Liverpool",away:"Chelsea",live:false,score:"vs"},
{country:"Germany",flag:"🇩🇪",league:"Bundesliga",home:"Bayern",away:"Dortmund",live:false,score:"vs"},
{country:"Denmark",flag:"🇩🇰",league:"Superliga",home:"Copenhagen",away:"Brondby",live:true,score:"2-1"},
{country:"Netherlands",flag:"🇳🇱",league:"Eredivisie",home:"Ajax",away:"PSV",live:false,score:"vs"},
{country:"Italy",flag:"🇮🇹",league:"Serie A",home:"Inter",away:"Milan",live:false,score:"vs"},
{country:"France",flag:"🇫🇷",league:"Ligue 1",home:"PSG",away:"Marseille",live:false,score:"vs"},
{country:"Saudi Arabia",flag:"🇸🇦",league:"Saudi Pro",home:"Al Nassr",away:"Al Hilal",live:false,score:"vs"},
{country:"Turkey",flag:"🇹🇷",league:"Super Lig",home:"Galatasaray",away:"Fenerbahce",live:false,score:"vs"},
{country:"Sweden",flag:"🇸🇪",league:"Allsvenskan",home:"Malmo",away:"AIK",live:false,score:"vs"},
{country:"Europe",flag:"🇪🇺",league:"Champions League",home:"Real Madrid",away:"Barcelona",live:false,score:"vs"},
];
function render(){
 let g={}; data.forEach(x=>{ if(!g[x.country]) g[x.country]=[]; g[x.country].push(x); });
 let h='';
 for(let c in g){
  let gl=g[c];
  h+=`<div class='country' onclick='this.classList.toggle("open")'><span>${gl[0].flag} ${c} (${gl.length}) ${gl.some(x=>x.live)?'🔴 LIVE':''}</span><span>›</span></div><div class='country'>`;
  gl.forEach((f,i)=>{
   let uid=c+i;
   h+=`<div class='fix' style='${f.live?"border-left-color:#ff4444":""}' onclick='event.stopPropagation();let b=document.getElementById("s-${uid}");b.classList.toggle("open");if(!b.dataset.l){fetch("/api/stats?home="+f.home+"&away="+f.away).then(r=>r.json()).then(j=>{b.innerHTML=j.html;b.dataset.l=1})}'><b>${f.home}</b> vs <b>${f.away}</b> <span style='float:right;color:#ffcc00'>${f.score} ${f.live?"🔴 LIVE":""}</span><br><small style='color:#8a96a8'>${f.league} • TAP FOR STATS</small></div><div class='stats' id='s-${uid}'>Loading stats...</div>`;
  });
  h+=`</div>`;
 }
 document.getElementById('list').innerHTML=h;
}
render();
function openTab(el,id){ let b=el.closest('.stats'); b.querySelectorAll('.mtab').forEach(t=>t.classList.remove('active')); el.classList.add('active'); b.querySelectorAll('.panel').forEach(p=>p.classList.remove('active')); b.querySelector('#'+id).classList.add('active'); }
</script></body></html>"""

@app.route("/api/stats")
def stats():
    home=request.args.get("home","Home"); away=request.args.get("away","Away")
    hs=team_stats(home); aw=team_stats(away)
    btts=min(85,max(30,int(55+(hs['g']+aw['g']-hs['c']-aw['c'])*10)))
    html=f"""<div><span class='mtab active' onclick='openTab(this,"g")'>General</span><span class='mtab' onclick='openTab(this,"h")'>H2H</span><span class='mtab' onclick='openTab(this,"p")'>Players</span><span class='mtab' onclick='openTab(this,"b")'>Best Bets %</span><span class='mtab' onclick='openTab(this,"a")'>AI</span></div>
<div class='panel active' id='g'>Goals: {home} {hs['g']} vs {away} {aw['g']}<br>Fouls: {hs['f']} vs {aw['f']}<br>SOT: {hs['sot']} vs {aw['sot']}<br>Corners: {hs['co']} vs {aw['co']}</div>
<div class='panel' id='h'>Pos: #{hs['pos']} vs #{aw['pos']}<br>Avg Cards {round((hs['ca']+aw['ca'])/2+0.5,1)} | Fouls {round((hs['f']+aw['f'])/2,1)} | Corners {round((hs['co']+aw['co'])/2,1)} | SOT {round((hs['sot']+aw['sot'])/2,1)}</div>
<div class='panel' id='p'>Shots L5: 2.8/g | Fouls 1.8/g | Cards 0.4/g | Tackles 3.2/g | Conv 18%</div>
<div class='panel' id='b'>BTTS {btts}% YES<br>Over 2.5 {60+btts//3}%<br>Over 8.5 Corners {int((hs['co']+aw['co'])*6)}%
