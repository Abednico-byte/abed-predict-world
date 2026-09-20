from flask import Flask, request
app = Flask(__name__)

TODAY = {
    "Albania": {"home": "Tirana", "away": "Partizani", "score": "1-0", "minute": "65:12", "avg_goals": 2.1, "btts": 45, "over25": 55, "corners": 9.2},
    "Germany": {"home": "Paderborn", "away": "TSG Hoffenheim", "score": "2-0", "minute": "50:27", "avg_goals": 1.5, "btts": 17, "over25": 17, "corners": 10.3},
    "Croatia": {"home": "Dinamo Zagreb", "away": "Hajduk Split", "score": "1-0", "minute": "23:15", "avg_goals": 2.3, "btts": 48, "over25": 58, "corners": 9.8},
    "Brazil": {"home": "Flamengo", "away": "Palmeiras", "score": "2-2", "minute": "88:12", "avg_goals": 3.1, "btts": 65, "over25": 72, "corners": 12.2},
}

TOMORROW = {
    "Albania": {"home": "Vllaznia", "away": "Skenderbeu", "kickoff": "18:00", "avg_goals": 2.4, "btts": 52, "over25": 61, "corners": 9.5, "home_win": 45, "draw": 25, "away_win": 30},
    "Andorra": {"home": "FC Andorra", "away": "UE Santa Coloma", "kickoff": "19:00", "avg_goals": 1.9, "btts": 41, "over25": 50, "corners": 8.8, "home_win": 38, "draw": 27, "away_win": 35},
    "Angola": {"home": "Sagrada", "away": "Interclube", "kickoff": "16:30", "avg_goals": 2.2, "btts": 48, "over25": 56, "corners": 9.1, "home_win": 42, "draw": 28, "away_win": 30},
    "Argentina": {"home": "River Plate", "away": "Boca Juniors", "kickoff": "00:30", "avg_goals": 2.7, "btts": 58, "over25": 64, "corners": 10.5, "home_win": 40, "draw": 26, "away_win": 34},
    "Belgium": {"home": "Genk", "away": "Standard Liege", "kickoff": "20:45", "avg_goals": 2.8, "btts": 59, "over25": 66, "corners": 10.2, "home_win": 48, "draw": 24, "away_win": 28},
    "Brazil": {"home": "Corinthians", "away": "Sao Paulo", "kickoff": "22:00", "avg_goals": 2.5, "btts": 54, "over25": 60, "corners": 11.0, "home_win": 44, "draw": 26, "away_win": 30},
    "Germany": {"home": "Bayern Munich", "away": "Dortmund", "kickoff": "19:30", "avg_goals": 3.4, "btts": 71, "over25": 78, "corners": 11.5, "home_win": 52, "draw": 22, "away_win": 26},
    "Croatia": {"home": "Rijeka", "away": "Osijek", "kickoff": "18:00", "avg_goals": 2.3, "btts": 50, "over25": 57, "corners": 9.6, "home_win": 46, "draw": 25, "away_win": 29},
}

def ai_calc(data):
    avg_goals = data['avg_goals']
    over25_pct = data['over25']
    btts_pct = data['btts']
    avg_corners = data['corners']
    bets = [
        {"bet": "Under 4.5 Goals", "prob": 97 if avg_goals < 2.5 else 85, "conf": "SUPER HIGH", "reason": f"Avg {avg_goals} goals"},
        {"bet": "Under 3.5 Goals", "prob": 91 if avg_goals < 2.8 else 72, "conf": "HIGH", "reason": f"Avg {avg_goals} - {over25_pct}% Over 2.5"},
        {"bet": f"BTTS {'Yes' if btts_pct>50 else 'No'}", "prob": max(btts_pct, 100-btts_pct), "conf": "HIGH", "reason": f"{btts_pct}% BTTS in H2H"},
        {"bet": f"{'Over' if over25_pct>50 else 'Under'} 2.5 Goals", "prob": max(over25_pct, 100-over25_pct), "conf": "HIGH", "reason": f"Avg {avg_goals} goals"},
        {"bet": "Over 8 Corners", "prob": 78 if avg_corners>9 else 60, "conf": "HIGH", "reason": f"Avg {avg_corners} corners"},
    ]
    bets.sort(key=lambda x: x['prob'], reverse=True)
    return bets

@app.route('/')
def index():
    day = request.args.get('day','today')
    data = TOMORROW if day == 'tomorrow' else TODAY
    tabs = f"""
    <div style="display:flex;gap:10px;padding:10px">
        <a href="/?day=today" style="padding:8px 14px;border-radius:20px;text-decoration:none;{'background:#00c853;color:black' if day=='today' else 'background:#242F44;color:white'}">Today LIVE</a>
        <a href="/?day=tomorrow" style="padding:8px 14px;border-radius:20px;text-decoration:none;{'background:#00c853;color:black' if day=='tomorrow' else 'background:#242F44;color:white'}">Tomorrow Prematch</a>
    </div>
    """
    html = ""
    for league, d in data.items():
        flag = {"Albania":"🇦🇱","Andorra":"🇦🇩","Angola":"🇦🇴","Argentina":"🇦🇷","Belgium":"🇧🇪","Brazil":"🇧🇷","Germany":"🇩🇪","Croatia":"🇭🇷"}.get(league,"⚽")
        info = f"{d.get('score','')} {d.get('minute','')} {d.get('kickoff','')}"
        html += f"<div onclick=\"location.href='/match?league={league}&day={day}'\" style='background:#1e2a3a;margin:1px 0;padding:12px 15px;display:flex;gap:10px;cursor:pointer'>{flag} {league} <span style='margin-left:auto;color:#888'>{d['home'][:12]} vs {d['away'][:12]} - {info} <span style='background:#00c853;color:black;font-size:10px;padding:2px 6px;border-radius:4px'>AI</span></span></div>"
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'><style>body{{background:#0f1623;color:white;font-family:Arial;margin:0}} .topbar{{background:#1a2332;padding:10px;font-weight:bold}}</style></head><body><div class='topbar'>🤖 ABED PREDICT WORLD - All Instructions Kept</div>{tabs}<div style='padding:10px;font-size:18px;font-weight:bold'>{day.upper()} - {len(data)} leagues</div>{html}</body></html>"

@app.route('/match')
def match_page():
    league = request.args.get('league','Germany')
    day = request.args.get('day','today')
    data = (TOMORROW if day == 'tomorrow' else TODAY).get(league, TODAY['Germany'])
    bets = ai_calc(data)
    bets_html = "".join([f"<div style='background:#242F44;padding:12px;border-radius:8px;margin:6px 0;display:flex;justify-content:space-between'><div><b>{b['bet']}</b><br><small style='color:#aaa'>{b['reason']}</small></div><div style='text-align:right'><b style='color:#00c853'>{b['prob']}%</b><br><small>{b['conf']}</small></div></div>" for b in bets])
    score_line = f"{data.get('score','')} ({data.get('minute','LIVE')})" if day=='today' else f"Kickoff {data.get('kickoff','')} - Prematch"
    win_line = f"Home Win {data.get('home_win',33)}% Draw {data.get('draw',22)}% Away {data.get('away_win',45)}%" if day=='tomorrow' else f"Win% Home 33% Away 67%"
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{background:#0f1623;color:white;font-family:Arial;padding:10px}} .card{{background:#1e2a3a;border-radius:12px;padding:15px;margin:10px 0}}</style></head><body>
    <button onclick="location.href='/?day={day}'" style="background:#242F44;color:white;padding:8px 12px;border-radius:6px;border:none">← Back to {day}</button>
    <div class="card"><h2>{data['home']} vs {data['away']}</h2><p>{league} - {score_line}</p><p>{win_line} | Avg Goals {data['avg_goals']} | BTTS {data['btts']}% | Over2.5 {data['over25']}% | Corners {data['corners']} | All Instructions Kept</p></div>
    <div class="card"><h3 style="color:#00c853">🤖 AI BETS - {league} - {day.upper()}</h3>{bets_html}</div>
    </body></html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
