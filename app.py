from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    grouped = {
        "Europe": {
            "Spain-LaLiga": {
                "league": "LaLiga", "country": "Spain", "type": "🏟️ LEAGUE",
                "teams": ["Barcelona", "Real Madrid", "Atletico Madrid", "Getafe", "Malaga", "Sevilla"],
                "scorers": [{"name": "Lewandowski", "goals": 12}, {"name": "Mbappe", "goals": 10}],
                "games": [
                    {"home": "Getafe", "away": "Malaga", "score": "1-0", "time": "09-20 14:00", "live": False, "finished": True},
                    {"home": "Atletico Madrid", "away": "Real Madrid", "score": "vs", "time": "09-22 20:00", "live": False, "finished": False},
                    {"home": "Barcelona", "away": "Sevilla", "score": "vs", "time": "09-24 18:30", "live": False, "finished": False},
                    {"home": "Villarreal", "away": "Betis", "score": "vs", "time": "09-25 21:00", "live": False, "finished": False}
                ]
            },
            "England-FA Cup": {
                "league": "FA Cup", "country": "England", "type": "🏆 CUP",
                "teams": ["Man City", "Arsenal", "Liverpool"],
                "scorers": [{"name": "Salah", "goals": 4}],
                "games": [
                    {"home": "Man City", "away": "Arsenal", "score": "vs", "time": "09-24 19:45", "live": False, "finished": False},
                    {"home": "Chelsea", "away": "Tottenham", "score": "vs", "time": "09-26 19:00", "live": False, "finished": False}
                ]
            },
            "England-Championship": {
                "league": "Championship", "country": "England", "type": "🌱 AMATEUR",
                "teams": ["Leeds", "Burnley"],
                "scorers": [{"name": "Piroe", "goals": 6}],
                "games": [
                    {"home": "Leeds", "away": "Burnley", "score": "vs", "time": "09-21 16:00", "live": False, "finished": False}
                ]
            }
        },
        "Africa": {
            "South Africa-PSL": {
                "league": "PSL", "country": "South Africa", "type": "🏟️ LEAGUE",
                "teams": ["Mamelodi Sundowns", "Orlando Pirates", "Kaizer Chiefs"],
                "scorers": [{"name": "Shalulile", "goals": 8}],
                "games": [
                    {"home": "Sundowns", "away": "Pirates", "score": "vs", "time": "09-21 19:00", "live": False, "finished": False},
                    {"home": "Chiefs", "away": "CT City", "score": "vs", "time": "09-23 18:00", "live": False, "finished": False}
                ]
            }
        },
        "Asia": {
            "Saudi-Saudi Pro": {
                "league": "Saudi Pro League", "country": "Saudi-Arabia", "type": "🏟️ LEAGUE",
                "teams": ["Al Nassr", "Al Hilal"],
                "scorers": [{"name": "Ronaldo", "goals": 11}],
                "games": [
                    {"home": "Al Nassr", "away": "Al Hilal", "score": "vs", "time": "09-22 20:30", "live": False, "finished": False}
                ]
            }
        }
    }
    total = 9
    return render_template("index.html", grouped_games=grouped, today=f"{datetime.now().strftime('%Y-%m-%d')} + 7 days ({total} games) - SAFE MODE")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
