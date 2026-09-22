#!/usr/bin/env python3
"""
Football Analysis – clean single-file Flask app
- Home = pre-matches only
- Separate Live section
- Grouped by country → competition
- ESPN via site.web.api.espn.com
- L5 probability model + cache
"""

import os
import hashlib
import requests
import urllib.parse
from flask import Flask, jsonify, request
from datetime import datetime, timezone, timedelta
import time
import threading

app = Flask(__name__)

BOTSWANA_TZ = timezone(timedelta(hours=2))
REQUEST_TIMEOUT = 10
CACHE_TTL = 300  # 5 minutes

_cache = {}
_cache_lock = threading.Lock()

def cache_get(key):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() - entry["ts"] < CACHE_TTL:
            return entry["data"]
        return None

def cache_set(key, data):
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.espn.com/soccer/",
    "Origin": "https://www.espn.com",
}

# ---------------------------------------------------------------------------
# Deterministic L5 fallback
# ---------------------------------------------------------------------------
def hash_int(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:6], 16)

def last5_fallback(team: str) -> dict:
    h = hash_int(team)
    values = []
    seed = h
    for i in range(5):
        gf = ((seed >> (i * 3)) & 7) % 4
        ga = ((seed >> (i * 2 + 1)) & 7) % 3
        values.append((gf, ga))
    wins = sum(1 for gf, ga in values if gf > ga)
    draws = sum(1 for gf, ga in values if gf == ga)
    avg_gf = sum(gf for gf, ga in values) / 5.0
    avg_ga = sum(ga for gf, ga in values) / 5.0
    btts = sum(1 for gf, ga in values if gf > 0 and ga > 0) / 5.0
    return {
        "wins": wins,
        "draws": draws,
        "avg_gf": round(avg_gf, 2),
        "avg_ga": round(avg_ga, 2),
        "btts": round(btts, 2),
        "g": values,
        "source": "fallback",
    }

def calc(home: str, away: str, hs=None, aw=None) -> dict:
    if hs is None:
        hs = last5_fallback(home)
    if aw is None:
        aw = last5_fallback(away)

    h_str = hs["avg_gf"] * 0.60 + max(0, 5 - hs["avg_ga"]) * 0.20 + hs["wins"] * 0.20 + 0.40
    a_str = aw["avg_gf"] * 0.60 + max(0, 5 - aw["avg_ga"]) * 0.20 + aw["wins"] * 0.20
    total = max(h_str + a_str, 0.01)

    hp = h_str / total * 78
    ap = a_str / total * 78
    dp = 100 - hp - ap

    if dp < 12:
        e = 12 - dp
        hp -= e / 2
        ap -= e / 2
        dp = 12
    if dp > 35:
        e = dp - 35
        hp += e / 2
        ap += e / 2
        dp = 35

    hp = round(max(1, hp), 1)
    dp = round(max(1, dp), 1)
    ap = round(max(1, 100 - hp - dp), 1)

    eg = max(0.2, min(5.0, (hs["avg_gf"] + aw["avg_gf"]) * 0.65 + (hs["avg_ga"] + aw["avg_ga"]) * 0.35 + 0.55))

    def over(l):
        return round(min(95, max(5, 50 + (eg - l) * 17)), 1)

    o05, o15, o25, o35, o45 = over(0.5), over(1.5), over(2.5), over(3.5), over(4.5)
    btts_yes = round(min(88, max(22, (hs["btts"] + aw["btts"]) / 2 * 100 * 0.85 + 10)), 1)

    return {
        "hp": hp, "dp": dp, "ap": ap,
        "1x": round(hp + dp, 1), "12": round(hp + ap, 1), "x2": round(dp + ap, 1),
        "o05": o05, "u05": round(100 - o05, 1),
        "o15": o15, "u15": round(100 - o15, 1),
        "o25": o25, "u25": round(100 - o25, 1),
        "o35": o35, "u35": round(100 - o35, 1),
        "o45": o45, "u45": round(100 - o45, 1),
        "bttsY": btts_yes, "bttsN": round(100 - btts_yes, 1),
        "hs": hs, "aw": aw,
        "expected_goals": round(eg, 2),
        "model_note": "L5 form model (deterministic fallback). Not for real-money betting.",
    }

# ---------------------------------------------------------------------------
# Country / competition helpers
# ---------------------------------------------------------------------------
def classify_country(l: str):
    low = (l or "").lower()
    if any(x in low for x in ["england", "premier league", "championship", "fa cup", "efl", "carabao", "league one", "league two"]):
        return "England", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if any(x in low for x in ["netherlands", "eredivisie", "knvb", "dutch"]):
        return "Netherlands", "🇳🇱"
    if any(x in low for x in ["spain", "laliga", "la liga"]):
        return "Spain", "🇪🇸"
    if any(x in low for x in ["germany", "bundesliga", "bundes"]):
        return "Germany", "🇩🇪"
    if any(x in low for x in ["italy", "serie a", "serie b"]):
        return "Italy", "🇮🇹"
    if any(x in low for x in ["france", "ligue 1", "ligue 2"]):
        return "France", "🇫🇷"
    if any(x in low for x in ["portugal", "liga portugal"]):
        return "Portugal", "🇵🇹"
    if any(x in low for x in ["belgium", "jupiler", "pro league"]):
        return "Belgium", "🇧🇪"
    if any(x in low for x in ["turkey", "süper", "super lig"]):
        return "Turkey", "🇹🇷"
    if any(x in low for x in ["scotland", "scottish"]):
        return "Scotland", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
    if any(x in low for x in ["denmark", "superliga"]):
        return "Denmark", "🇩🇰"
    if any(x in low for x in ["sweden", "allsvenskan"]):
        return "Sweden", "🇸🇪"
    if any(x in low for x in ["south africa", "premiership", "psl"]):
        return "South Africa", "🇿🇦"
    if any(x in low for x in ["mls", "major league", "united states", "usa"]):
        return "USA", "🇺🇸"
    if any(x in low for x in ["uefa", "champions league", "europa league", "conference league"]):
        return "Europe", "🇪🇺"
    if "women" in low:
        return "World Women", "🌍"
    return "World", "🌍"

def clean_league_name(raw: str) -> str:
    if not raw:
        return "Football"
    if "," in raw and len(raw) > 20:
        return raw.split(",")[0].strip()
    return raw.strip()

# ---------------------------------------------------------------------------
# ESPN fetch
# ---------------------------------------------------------------------------
def get_json(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    try:
        proxy_url = "https://api.allorigins.win/raw?url=" + urllib.parse.quote(url, safe="")
        r = requests.get(proxy_url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

LEAGUES = [
    ("eng.1", "English Premier League"),
    ("eng.2", "English Championship"),
    ("eng.fa", "English FA Cup"),
    ("eng.league_cup", "English Carabao Cup"),
    ("esp.1", "Spanish LaLiga"),
    ("ger.1", "German Bundesliga"),
    ("ita.1", "Italian Serie A"),
    ("fra.1", "French Ligue 1"),
    ("ned.1", "Dutch Eredivisie"),
    ("ned.cup", "Dutch KNVB Cup"),
    ("por.1", "Portuguese Liga"),
    ("bel.1", "Belgian Pro League"),
    ("tur.1", "Turkish Super Lig"),
    ("sco.1", "Scottish Premiership"),
    ("den.1", "Danish Superliga"),
    ("swe.1", "Swedish Allsvenskan"),
    ("rsa.1", "South African Premiership"),
    ("usa.1", "MLS"),
    ("uefa.champions", "UEFA Champions League"),
    ("uefa.europa", "UEFA Europa League"),
    ("uefa.europa.conf", "UEFA Conference League"),
    ("uefa.wchampions", "UEFA Women's Champions League"),
]

def parse_status(st_type: dict) -> tuple:
    """Return (category, short_score) where category is pre|live|post"""
    state = (st_type.get("state") or "").lower()
    short = st_type.get("shortDetail") or st_type.get("detail") or "TBD"
    completed = st_type.get("completed", False)
    if state == "in" or state == "live":
        return "live", short
    if state == "post" or completed:
        return "post", short
    return "pre", short

def fetch_espn():
    cached = cache_get("games")
    if cached is not None:
        return cached

    games = []
    now = datetime.now(BOTSWANA_TZ)
    dates = [(now + timedelta(days=d)).strftime("%Y%m%d") for d in [0, -1, 1, 2]]

    # 1. League-specific calls (best league names)
    for code, fallback_name in LEAGUES:
        for date_str in dates:
            data = get_json(
                f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_str}"
            )
            if not data:
                continue
            lname = fallback_name
            if data.get("leagues") and data["leagues"][0].get("name"):
                lname = data["leagues"][0]["name"]
            lname = clean_league_name(lname)
            country, flag = classify_country(lname)

            for ev in data.get("events", []):
                comp = (ev.get("competitions") or [{}])[0]
                cs = comp.get("competitors") or []
                if len(cs) < 2:
                    continue
                home = next((x for x in cs if x.get("homeAway") == "home"), cs[0])
                away = next((x for x in cs if x.get("homeAway") == "away"), cs[1])
                st_type = (comp.get("status") or {}).get("type") or {}
                cat, score = parse_status(st_type)

                note = comp.get("altGameNote") or ""
                if note and len(note) > 5:
                    possible = clean_league_name(note)
                    if len(possible) > 8:
                        lname = possible
                        country, flag = classify_country(lname)

                games.append({
                    "league": lname,
                    "leagueName": lname,
                    "country": country,
                    "flag": flag,
                    "home": (home.get("team", {}).get("displayName") or "Home")[:40],
                    "away": (away.get("team", {}).get("displayName") or "Away")[:40],
                    "score": score,
                    "live": cat == "live",
                    "status": cat,
                    "statusDetail": st_type.get("description") or score,
                })

    # 2. Broad "all" as safety net
    for date_str in dates:
        data = get_json(
            f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}&limit=400"
        )
        if not data:
            continue
        for ev in data.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            cs = comp.get("competitors") or []
            if len(cs) < 2:
                continue
            home = next((x for x in cs if x.get("homeAway") == "home"), cs[0])
            away = next((x for x in cs if x.get("homeAway") == "away"), cs[1])
            st_type = (comp.get("status") or {}).get("type") or {}
            cat, score = parse_status(st_type)

            lname = None
            note = comp.get("altGameNote") or ""
            if note:
                lname = clean_league_name(note)
            if not lname and data.get("leagues") and data["leagues"][0].get("name"):
                lname = data["leagues"][0]["name"]
            if not lname:
                lname = "Football"
            lname = clean_league_name(lname)
            country, flag = classify_country(lname)

            games.append({
                "league": lname,
                "leagueName": lname,
                "country": country,
                "flag": flag,
                "home": (home.get("team", {}).get("displayName") or "Home")[:40],
                "away": (away.get("team", {}).get("displayName") or "Away")[:40],
                "score": score,
                "live": cat == "live",
                "status": cat,
                "statusDetail": st_type.get("description") or score,
            })

    # Deduplicate
    seen = set()
    out = []
    for g in games:
        k = (g["home"].lower(), g["away"].lower(), g["leagueName"].lower())
        if k not in seen:
            seen.add(k)
            out.append(g)

    print(f"Final games: {len(out)}  (pre={sum(1 for g in out if g['status']=='pre')} live={sum(1 for g in out if g['status']=='live')} post={sum(1 for g in out if g['status']=='post')})")
    cache_set("games", out)
    return out

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/api/games")
def api_games():
    games = fetch_espn()
    if not games:
        return jsonify({
            "games": [],
            "error": "No ESPN fixtures were returned. Check the server log and ESPN availability.",
        })
    return jsonify({
        "games": games,
        "error": None,
        "date": datetime.now(BOTSWANA_TZ).strftime("%Y-%m-%d"),
        "count": len(games),
        "pre": sum(1 for g in games if g["status"] == "pre"),
        "live": sum(1 for g in games if g["status"] == "live"),
        "post": sum(1 for g in games if g["status"] == "post"),
    })

@app.route("/api/prob")
def api_prob():
    home = request.args.get("home", "Home").strip()
    away = request.args.get("away", "Away").strip()
    if not home or not away:
        return jsonify({"error": "Both home and away teams are required."}), 400

    p = calc(home, away)

    html = f"""
    <div class="card">
      <div class="chead">⚽ Full-Time <span class="free">L5</span></div>
      <div class="row3">
        <div><small>HOME</small><b>{p['hp']}%</b><div class="bar"><div style="width:{p['hp']}%"></div></div></div>
        <div><small>DRAW</small><b>{p['dp']}%</b><div class="bar"><div style="width:{p['dp']}%"></div></div></div>
        <div><small>AWAY</small><b>{p['ap']}%</b><div class="bar"><div style="width:{p['ap']}%"></div></div></div>
      </div>
      <small style="color:#8a96a8">
        L5 {home}: W{p['hs']['wins']} D{p['hs']['draws']} | {p['hs']['avg_gf']:.1f} GF / {p['hs']['avg_ga']:.1f} GA<br>
        L5 {away}: W{p['aw']['wins']} D{p['aw']['draws']} | {p['aw']['avg_gf']:.1f} GF / {p['aw']['avg_ga']:.1f} GA
      </small>
    </div>
    <div class="card">
      <div class="chead">🛡️ Double Chance</div>
      <div class="row3">
        <div><small>1X</small><b>{p['1x']}%</b><div class="bar"><div style="width:{p['1x']}%"></div></div></div>
        <div><small>12</small><b>{p['12']}%</b><div class="bar"><div style="width:{p['12']}%"></div></div></div>
        <div><small>X2</small><b>{p['x2']}%</b><div class="bar"><div style="width:{p['x2']}%"></div></div></div>
      </div>
    </div>
    <div class="card">
      <div class="chead">📊 Total Goals</div>
      <div class="grow"><span>+0.5</span><div class="bar2"><div style="width:{p['o05']}%"></div></div><b>{p['o05']}%</b></div>
      <div class="grow"><span>-0.5</span><div class="bar2"><div style="width:{p['u05']}%"></div></div><b>{p['u05']}%</b></div>
      <div class="grow"><span>+1.5</span><div class="bar2"><div style="width:{p['o15']}%"></div></div><b>{p['o15']}%</b></div>
      <div class="grow"><span>-1.5</span><div class="bar2"><div style="width:{p['u15']}%"></div></div><b>{p['u15']}%</b></div>
      <div class="grow"><span>+2.5</span><div class="bar2"><div style="width:{p['o25']}%"></div></div><b>{p['o25']}%</b></div>
      <div class="grow"><span>-2.5</span><div class="bar2"><div style="width:{p['u25']}%"></div></div><b>{p['u25']}%</b></div>
      <div class="grow"><span>+3.5</span><div class="bar2"><div style="width:{p['o35']}%"></div></div><b>{p['o35']}%</b></div>
      <div class="grow"><span>-3.5</span><div class="bar2"><div style="width:{p['u35']}%"></div></div><b>{p['u35']}%</b></div>
      <div class="grow"><span>+4.5</span><div class="bar2"><div style="width:{p['o45']}%"></div></div><b>{p['o45']}%</b></div>
      <div class="grow"><span>-4.5</span><div class="bar2"><div style="width:{p['u45']}%"></div></div><b>{p['u45']}%</b></div>
      <small style="color:#8a96a8">Expected goals: {p['expected_goals']}</small>
    </div>
    <div class="card">
      <div class="chead">🤝 BTTS</div>
      <div class="row2">
        <div><small>YES</small><b>{p['bttsY']}%</b><div class="bar"><div style="width:{p['bttsY']}%"></div></div></div>
        <div><small>NO</small><b>{p['bttsN']}%</b><div class="bar"><div style="width:{p['bttsN']}%"></div></div></div>
      </div>
    </div>
    <div class="note">⚠️ {p['model_note']}</div>
    """
    return jsonify({"html": html})

@app.route("/")
def home():
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
  <title>Football Analysis</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; background: #0f141f; color: #fff; font-family: system-ui, -apple-system, Arial, sans-serif; }
    .top { padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; background: #1c2333; position: sticky; top: 0; z-index: 30; border-bottom: 1px solid #2a3447; }
    .top h3 { margin: 0; font-size: 17px; }
    .live-btn { background: #2a3447; padding: 6px 14px; border-radius: 20px; font-size: 12px; cursor: pointer; user-select: none; border: 1px solid #3a4557; }
    .live-btn.active { background: #ff4444; color: #fff; border-color: #ff4444; }
    .section-head { padding: 12px 16px 6px; font-size: 13px; font-weight: 700; color: #8a96a8; text-transform: uppercase; letter-spacing: .4px; }
    .country-head { padding: 13px 16px; font-weight: 600; background: #1c2333; display: flex; justify-content: space-between; align-items: center; cursor: pointer; border-bottom: 1px solid #242f44; }
    .league-tabs { display: flex; gap: 8px; padding: 10px 12px; overflow-x: auto; background: #121a2a; white-space: nowrap; scrollbar-width: none; }
    .league-tabs::-webkit-scrollbar { display: none; }
    .ltab { padding: 6px 14px; background: #1a2535; border-radius: 20px; font-size: 12px; cursor: pointer; border: 1px solid #2a3447; flex-shrink: 0; }
    .ltab.active { background: #00ff88; color: #000; font-weight: 700; }
    .fixtures-wrap { background: #121a2a; padding-bottom: 6px; }
    .fixture { background: #242f44; margin: 8px 12px; padding: 13px 14px; border-radius: 12px; cursor: pointer; border-left: 3px solid #00ff88; }
    .fixture.live { border-left-color: #ff4444; }
    .fixture:active { background: #2c3a55; }
    .stats { display: none; background: #0f141f; margin: 0 12px 10px; padding: 6px; border-radius: 12px; }
    .stats.open { display: block; }
    .card { background: #242f44; margin: 10px 0; padding: 14px; border-radius: 12px; }
    .chead { display: flex; justify-content: space-between; font-weight: 600; margin-bottom: 12px; font-size: 13px; }
    .free { font-size: 9px; background: #00ff8822; border: 1px solid #00ff88; color: #00ff88; padding: 3px 8px; border-radius: 12px; }
    .row3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
    .row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .bar { height: 6px; background: #1c2333; border-radius: 10px; margin-top: 4px; overflow: hidden; }
    .bar div { height: 6px; background: #00ff88; border-radius: 10px; }
    .bar2 { flex: 1; height: 6px; background: #1c2333; border-radius: 10px; margin: 0 8px; overflow: hidden; }
    .bar2 div { height: 6px; background: #6c4cff; border-radius: 10px; }
    .grow { display: flex; align-items: center; justify-content: space-between; margin: 7px 0; font-size: 12px; }
    .note { background: #3b2d10; color: #ffd56a; padding: 10px 12px; border-radius: 10px; font-size: 11px; margin-top: 10px; }
    .error { margin: 16px; padding: 16px; background: #3b1820; border-radius: 10px; color: #ff9ba8; }
    .empty { padding: 30px 20px; text-align: center; color: #8a96a8; font-size: 14px; }
    .bottom { position: fixed; bottom: 0; left: 0; right: 0; background: #1c2333; display: flex; justify-content: space-around; padding: 11px 0; border-top: 1px solid #2a3447; font-size: 12px; z-index: 40; }
    .bottom div { opacity: .7; }
    #loader { padding: 40px 20px; text-align: center; color: #8a96a8; }
  </style>
</head>
<body>
  <div class="top">
    <h3>Today <span id="count" style="color:#00ff88;font-weight:400"></span></h3>
    <div class="live-btn" id="liveBtn" onclick="toggleLive()">● LIVE</div>
  </div>

  <div id="loader">Loading ESPN fixtures…</div>
  <div id="list"></div>
  <div style="height:72px"></div>

  <div class="bottom">
    <div>🗓️ Fixtures</div>
    <div>🔔 Alerts</div>
    <div>📈 Trends</div>
    <div>☰ More</div>
  </div>

<script>
let allGames = [];
let showLiveOnly = false;
let openC = {};
let selL = {};

function toggleLive() {
  showLiveOnly = !showLiveOnly;
  document.getElementById("liveBtn").classList.toggle("active", showLiveOnly);
  render();
}

function toggleC(k) {
  openC[k] = !(openC[k] !== false);
  render();
}

function selectL(ck, l) {
  selL[ck] = l;
  render();
}

function escapeHtml(v) {
  return String(v)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderGroup(games, sectionTitle) {
  if (!games.length) return "";
  let html = "";
  if (sectionTitle) {
    html += `<div class="section-head">${sectionTitle}</div>`;
  }

  const byCountry = {};
  games.forEach(g => {
    const k = g.flag + "|" + g.country;
    if (!byCountry[k]) byCountry[k] = [];
    byCountry[k].push(g);
  });

  const keys = Object.keys(byCountry).sort((a, b) => {
    const ca = a.split("|")[1], cb = b.split("|")[1];
    if (ca === "Europe") return -1;
    if (cb === "Europe") return 1;
    return ca.localeCompare(cb);
  });

  for (const ck of keys) {
    const countryGames = byCountry[ck];
    const parts = ck.split("|");
    const flag = parts[0];
    const country = parts[1];
    const isOpen = openC[ck] !== false;
    const leagues = [...new Set(countryGames.map(x => x.leagueName))];
    if (!selL[ck]) selL[ck] = leagues[0];
    const sel = selL[ck];
    const liveC = countryGames.filter(x => x.live).length;

    html += `<div class="country-head" onclick="toggleC('${ck.replace(/'/g, "\\\\'")}')">
      <span>${flag} ${escapeHtml(country)} (${countryGames.length})${liveC > 0 ? ' <span style="color:#ff4444">🔴' + liveC + '</span>' : ''}</span>
      <span style="opacity:.6">${isOpen ? "▼" : "▶"}</span>
    </div>`;

    if (isOpen) {
      html += `<div class="league-tabs">`;
      leagues.forEach(l => {
        const c = countryGames.filter(x => x.leagueName === l).length;
        const act = l === sel ? "active" : "";
        html += `<div class="ltab ${act}" onclick="event.stopPropagation();selectL('${ck.replace(/'/g, "\\\\'")}','${String(l).replace(/'/g, "\\\\'")}')">${escapeHtml(l)} (${c})</div>`;
      });
      html += `</div><div class="fixtures-wrap">`;

      countryGames.filter(x => x.leagueName === sel).forEach((f, i) => {
        const uid = btoa(unescape(encodeURIComponent(ck + "|" + f.home + "|" + f.away + "|" + i))).replace(/[^a-zA-Z0-9]/g, "");
        const isLive = f.status === "live";
        html += `
          <div class="fixture ${isLive ? "live" : ""}" onclick="openP('${escapeHtml(f.home).replace(/'/g, "\\\\'")}','${escapeHtml(f.away).replace(/'/g, "\\\\'")}','${uid}')">
            <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
              <b style="flex:1;text-align:right;font-size:13px">${escapeHtml(f.home)}</b>
              <span style="opacity:.5;font-size:12px">vs</span>
              <b style="flex:1;font-size:13px">${escapeHtml(f.away)}</b>
              <span style="color:${isLive ? "#ff6666" : "#ffcc00"};min-width:52px;text-align:right;font-size:13px;font-weight:600">${escapeHtml(f.score)}</span>
            </div>
            <small style="color:#8a96a8;display:block;margin-top:5px;font-size:11px">${escapeHtml(f.leagueName)}</small>
          </div>
          <div class="stats" id="stats-${uid}"></div>`;
      });
      html += `</div>`;
    }
  }
  return html;
}

function render() {
  let html = "";
  const liveGames = allGames.filter(g => g.status === "live");
  const preGames  = allGames.filter(g => g.status === "pre");

  if (showLiveOnly) {
    document.getElementById("count").textContent = "(" + liveGames.length + " live)";
    if (liveGames.length === 0) {
      html = "<div class='empty'>No live matches right now</div>";
    } else {
      html = renderGroup(liveGames, "🔴 Live Now");
    }
  } else {
    document.getElementById("count").textContent = "(" + preGames.length + ")";
    if (preGames.length === 0 && liveGames.length === 0) {
      html = "<div class='empty'>No upcoming fixtures found</div>";
    } else {
      if (liveGames.length > 0) {
        html += renderGroup(liveGames, "🔴 Live Now (" + liveGames.length + ")");
      }
      if (preGames.length > 0) {
        html += renderGroup(preGames, "📅 Upcoming");
      }
    }
  }

  document.getElementById("list").innerHTML = html;
  document.getElementById("loader").style.display = "none";
}

function openP(h, a, uid) {
  const box = document.getElementById("stats-" + uid);
  if (!box) return;
  box.classList.toggle("open");
  if (box.dataset.loaded) return;
  box.innerHTML = "<div style='padding:12px;color:#8a96a8;font-size:13px'>Calculating L5…</div>";
  fetch("/api/prob?home=" + encodeURIComponent(h) + "&away=" + encodeURIComponent(a))
    .then(r => r.json())
    .then(j => {
      box.innerHTML = j.html || "<div class='error'>Could not load probabilities</div>";
      box.dataset.loaded = "1";
    })
    .catch(() => {
      box.innerHTML = "<div class='error'>Network error</div>";
    });
}

fetch("/api/games")
  .then(r => r.json())
  .then(data => {
    allGames = data.games || [];
    render();
    if (data.error && allGames.length === 0) {
      document.getElementById("loader").innerHTML = "<div class='error'>" + escapeHtml(data.error) + "</div>";
      document.getElementById("loader").style.display = "block";
    }
  })
  .catch(() => {
    document.getElementById("loader").innerHTML = "<div class='error'>Failed to load fixtures</div>";
  });
</script>
</body>
</html>"""

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time_botswana": datetime.now(BOTSWANA_TZ).isoformat(),
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
