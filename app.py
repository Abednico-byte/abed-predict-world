from flask import Flask, render_template

app = Flask(__name__)

LEAGUES = [
    {"id": "england-premier-league", "n": "England - Premier League"},
    {"id": "spain-laliga", "n": "Spain - LaLiga"},
    {"id": "germany-bundesliga", "n": "Germany - Bundesliga"},
    {"id": "italy-serie-a", "n": "Italy - Serie A"},
    {"id": "france-ligue-1", "n": "France - Ligue 1"},
    {"id": "netherlands-eredivisie", "n": "Netherlands - Eredivisie"},
    {"id": "portugal-primeira", "n": "Portugal - Primeira Liga"},
    {"id": "uefa-champions", "n": "Europe - Champions League"},
]

GAMES_BY_LEAGUE = {
    "england-premier-league": [
        {"id": "man-city-vs-arsenal", "home": "Man City vs Arsenal", "time": "17:30"},
        {"id": "liverpool-vs-chelsea", "home": "Liverpool vs Chelsea", "time": "19:45"},
        {"id": "man-utd-vs-tottenham", "home": "Man Utd vs Tottenham", "time": "14:00"},
    ],
    "spain-laliga": [
        {"id": "atletico-vs-sevilla", "home": "Atletico vs Sevilla", "time": "17:00"},
        {"id": "real-madrid-vs-barcelona", "home": "Real Madrid vs Barcelona", "time": "19:45"},
        {"id": "barcelona-vs-sevilla", "home": "Barcelona vs Sevilla", "time": "18:30"},
        {"id": "sevilla-vs-real-madrid", "home": "Sevilla vs Real Madrid", "time": "12:00"},
    ],
    "germany-bundesliga": [
        {"id": "bayern-vs-dortmund", "home": "Bayern vs Dortmund", "time": "18:30"},
        {"id": "leverkusen-vs-leipzig", "home": "Leverkusen vs Leipzig", "time": "15:30"},
    ],
    "italy-serie-a": [
        {"id": "inter-vs-milan", "home": "Inter vs AC Milan", "time": "19:45"},
        {"id": "juventus-vs-roma", "home": "Juventus vs Roma", "time": "17:00"},
    ],
    "france-ligue-1": [
        {"id": "psg-vs-marseille", "home": "PSG vs Marseille", "time": "19:45"},
        {"id": "lyon-vs-lille", "home": "Lyon vs Lille", "time": "17:00"},
    ],
    "netherlands-eredivisie": [
        {"id": "ajax-vs-psv", "home": "Ajax vs PSV", "time": "16:45"},
    ],
    "portugal-primeira": [
        {"id": "benfica-vs-porto", "home": "Benfica vs Porto", "time": "20:15"},
    ],
    "uefa-champions": [
        {"id": "real-vs-city", "home": "Real Madrid vs Man City", "time": "21:00"},
    ],
}

@app.route('/')
def index():
    return render_template('index.html', leagues=LEAGUES)

@app.route('/league/<league_id>')
def league_page(league_id):
    league = next((l for l in LEAGUES if l["id"] == league_id), {"id": league_id, "n": league_id.replace("-", " ").title()})
    games = GAMES_BY_LEAGUE.get(league_id, [])
    return render_template('league.html', lg=league, games=games)

@app.route('/game/<game_id>')
def game_page(game_id):
    name = game_id.replace("-", " ").title()
    return render_template('game.html', game=name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
