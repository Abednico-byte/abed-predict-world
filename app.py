from flask import Flask, render_template, jsonify

app = Flask(__name__)

FIXTURE = {
    "home": "Paderborn", "away": "TSG Hoffenheim",
    "score": "2-0", "minute": "50:27",
    "league": "Germany Bundesliga", "status": "Live"
}

H2H = {
    "win_pct": {"home": 33, "away": 67},
    "boxes": {"matches": 6, "avg_goals": 1.5, "btts_pct": 17, "over_25_pct": 17, "avg_corners": 10.3, "avg_cards": 2},
    "matches": [
        {"date": "2024-08-10", "home": "Paderborn", "away": "Hoffenheim", "score": "0-1", "poss": "38%-62%", "cards": "3-0", "corners": "2-8"},
        {"date": "2023-07-15", "home": "Hoffenheim", "away": "Paderborn", "score": "2-0", "poss": "55%-45%", "cards": "1-2", "corners": "6-4"},
        {"date": "2023-01-20", "home": "Paderborn", "away": "Hoffenheim", "score": "1-2", "poss": "42%-58%", "cards": "2-1", "corners": "3-7"},
    ]
}

PLAYERS = [
    {"no": 9, "name": "P. Conteh", "pos": "FW", "goals": 5, "minutes": 890, "win_rate": 25, "clean_sheets": 0, "rating": 6.83, "xg": 4.2, "xa": 1.1, "form": "↑"},
    {"no": 10, "name": "S. Klaas", "pos": "MF", "goals": 3, "minutes": 1020, "win_rate": 30, "clean_sheets": 0, "rating": 7.12, "xg": 2.8, "xa": 3.4, "form": "↑"},
    {"no": 1, "name": "M. Schubert", "pos": "GK", "goals": 0, "minutes": 1080, "win_rate": 25, "clean_sheets": 2, "rating": 6.95, "xg": 0, "xa": 0, "form": "→"},
]

PREDICTIONS = {
    "full_time": {"home": 38.5, "draw": 22.4, "away": 39.1},
    "double_chance": {"1X": 60.9, "12": 77.6, "X2": 61.5},
    "half_time": {"home": 30, "draw": 45, "away": 25},
    "total_goals": {"over_0_5": 88, "under_0_5": 12, "over_1_5": 62, "under_1_5": 38, "over_2_5": 22, "under_2_5": 78, "over_3_5": 9, "under_3_5": 91, "over_4_5": 3, "under_4_5": 97},
    "first_half_goals": {"over_0_5": 58, "under_0_5": 42},
    "btts": {"yes": 17, "no": 83},
    "home_goals": {"over_0_5": 38, "under_0_5": 62, "over_1_5": 12, "under_1_5": 88},
    "away_goals": {"over_0_5": 68, "under_0_5": 32, "over_1_5": 35, "under_1_5": 65},
    "corners": {"over_8": 78, "under_8": 22, "over_9": 68, "under_9": 32, "over_10": 52, "under_10": 48}
}

AI_BETS = [
    {"bet": "Under 4.5 Goals", "prob": 97, "conf": "SUPER HIGH", "color": "green", "reason": "Avg 1.5 goals"},
    {"bet": "Under 3.5 Goals", "prob": 91, "conf": "HIGH", "color": "green", "reason": "17% Over 2.5 in H2H"},
    {"bet": "Over 0.5 Goals", "prob": 88, "conf": "HIGH", "color": "green", "reason": "High scoring prob"},
    {"bet": "Home Under 1.5 Goals", "prob": 88, "conf": "HIGH", "color": "green", "reason": "Paderborn weak"},
    {"bet": "BTTS No", "prob": 83, "conf": "HIGH", "color": "green", "reason": "17% BTTS in H2H"},
    {"bet": "Under 2.5 Goals", "prob": 78, "conf": "HIGH", "color": "green", "reason": "Avg 1.5 goals"},
    {"bet": "Over 8 Corners", "prob": 78, "conf": "HIGH", "color": "green", "reason": "Avg 10.3 corners"},
    {"bet": "Away Over 0.5 Goals", "prob": 68, "conf": "MEDIUM", "color": "yellow", "reason": "67% wins"},
    {"bet": "Double Chance X2", "prob": 61.5, "conf": "MEDIUM", "color": "yellow", "reason": "Hoffenheim 67%"},
]

@app.route('/')
def index():
    return render_template('index.html', fixture=FIXTURE, h2h=H2H, players=PLAYERS, pred=PREDICTIONS, ai_bets=AI_BETS)

@app.route('/api/all')
def api_all():
    return jsonify({"fixture": FIXTURE, "h2h": H2H, "players": PLAYERS, "predictions": PREDICTIONS, "ai_bets": AI_BETS})
@app.route('/match')
def match_detail():
    league = request.args.get('league', 'Germany Bundesliga')
    # This opens your AI page you built - from screenshot 1
    FIXTURE = {"home": "Paderborn", "away": "TSG Hoffenheim", "score": "2-0", "minute": "50:27", "league": league}
    H2H = {"win_pct": {"home": 33, "away": 67}, "boxes": {"matches": 6, "avg_goals": 1.5, "btts_pct": 17, "over_25_pct": 17, "avg_corners": 10.3, "avg_cards": 2}, "matches": []}
    total_goals, btts, corners, ai_bets = ai_calculate_prob(H2H)
    PREDICTIONS = {"full_time": {"home": 38.5, "draw": 22.4, "away": 39.1}, "double_chance": {"1X": 60.9, "12": 77.6, "X2": 61.5}, "total_goals": total_goals, "btts": btts, "corners": corners}
    return render_template('match.html', fixture=FIXTURE, h2h=H2H, pred=PREDICTIONS, ai_bets=ai_bets)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
