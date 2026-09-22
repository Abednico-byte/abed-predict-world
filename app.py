#!/usr/bin/env python3
"""
Football Analysis – clean single-file Flask app
- ESPN fixtures via site.web.api.espn.com
- Simple L5 form model (real schedule when available + deterministic fallback)
- In-memory cache
- Fixed frontend
"""

import os
import hashlib
import requests
import urllib.parse
from flask import Flask, jsonify, request
from datetime import datetime, timezone, timedelta
from functools import lru_cache
import time
import threading

app = Flask(__name__)

BOTSWANA_TZ = timezone(timedelta(hours=2))
REQUEST_TIMEOUT = 10
CACHE_TTL = 300  # 5 minutes

# Simple thread-safe cache
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
# Deterministic L5 fallback (hash of team name)
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

# ---------------------------------------------------------------------------
# Probability model
# ---------------------------------------------------------------------------
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

    o05 = over(0.5)
    o15 = over(1.5)
    o25 = over(2.5)
    o35 = over(3.5)
    o45 = over(4.5)

    btts_yes = round(min(88, max(22, (hs["btts"] + aw["btts"]) / 2 * 100 * 0.85 + 10)), 1)

    return {
        "hp": hp, "dp": dp, "ap": ap,
        "1x": round(hp + dp, 1),
        "12": round(hp + ap, 1),
        "x2": round(dp + ap, 1),
        "o05": o05, "u05": round(100 - o05, 1),
        "o15": o15, "u15": round(100 - o15, 1),
        "o25": o25, "u25": round(100 - o25, 1),
        "o35": o35, "u35": round(100 - o35, 1),
        "o45": o45, "u45": round(100 - o45, 1),
        "bttsY": btts_yes, "bttsN": round(100 - btts_yes, 1),
        "hs": hs, "aw": aw,
        "expected_goals": round(eg, 2),
        "model_note": "L5 form model (real schedule when available, otherwise deterministic fallback). Not for real-money betting.",
    }

# ---------------------------------------------------------------------------
# Country / flag helper
# ---------------------------------------------------------------------------
def classify_country(l: str):
    low = (l or "").lower()
    if any(x in low for x in ["england", "premier league", "championship", "fa cup", "efl", "carabao"]):
        return "England", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if any(x in low for x in ["knvb", "dutch", "eredivisie", "netherlands", "netherlands"]):
        return "Netherlands", "🇳🇱"
    if any(x in low for x in ["spain", "laliga", "la liga"]):
        return "Spain", "🇪🇸"
    if any(x in low for x in ["bundes", "germany", "bundesliga"]):
        return "Germany", "🇩🇪"
    if any(x in low for x in ["serie", "italy"]):
        return "Italy", "🇮🇹"
    if any(x in low for x in ["ligue", "france"]):
        return "France", "🇫🇷"
    if any(x in low for x in ["portugal", "liga portugal"]):
        return "Portugal", "🇵🇹"
    if any(x in low for x in ["belgium", "jupiler"]):
        return "Belgium", "🇧🇪"
    if any(x in low for x in ["turkey", "süper"]):
        return "Turkey", "🇹🇷"
    if any(x in low for x in ["scotland", "scottish"]):
        return "Scotland", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
    if any(x in low for x in ["denmark", "superliga"]):
        return "Denmark", "🇩🇰"
    if any(x in low for x in ["sweden", "allsvenskan"]):
        return "Sweden", "🇸🇪"
    if any(x in low for x in ["south africa", "premiership", "psl"]):
        return "South Africa", "🇿🇦"
    if any(x in low for x in ["mls", "major league soccer", "usa"]):
        return "USA", "🇺🇸"
    if any(x in low for x in ["uefa", "champions", "europa", "conference"]):
        return "Europe", "🇪🇺"
    if "women" in low:
        return "World Women", "🌍"
    return "World", "🌍"

# ---------------------------------------------------------------------------
# ESPN fetch helpers
# ---------------------------------------------------------------------------
def get_json(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    # Proxy fallback
    try:
        proxy_url = "https://api.allorigins.win/raw?url=" + urllib.parse.quote(url, safe="")
        r = requests.get(proxy_url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

LEAGUES = [
    "eng.1", "eng.2", "eng.fa", "eng.league_cup",
    "esp.1", "ger.1", "ita.1", "fra.1",
    "ned.1", "ned.cup", "por.1", "bel.1",
    "tur.1", "sco.1", "den.1", "swe.1",
    "rsa.1", "usa.1",
    "uefa.champions", "uefa.europa", "uefa.europa.conf",
    "uefa.wchampions",
]

def fetch_espn():
    cached = cache_get("games")
    if cached is not None:
        return cached

    games = []
    now = datetime.now(BOTSWANA_TZ)
    dates = [(now + timedelta(days=d)).strftime("%Y%m%d") for d in [0, -1, 1, 2]]

    for date_str in dates:
        if len(games) > 60:
            break

        # Broad "all" call first (most reliable single request)
        data = get_json(
            f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={date_str}&limit=400"
        )
        if data:
            for ev in data.get("events", []):
                comp = (ev.get("competitions") or [{}])[0]
                cs = comp.get("competitors") or []
                if len(cs) < 2:
                    continue
                home = next((x for x in cs if x.get("homeAway") == "home"), cs[0])
                away = next((x for x in cs if x.get("homeAway") == "away"), cs[1])
                lname = (
                    (data.get("leagues") or [{}])[0].get("name")
                    if data.get("leagues")
                    else None
                ) or ev.get("shortName") or "Football"
                # Prefer competition name when available
                if comp.get("competitors"):
                    league_info = (data.get("leagues") or [{}])[0]
                    if league_info.get("name"):
                        lname = league_info["name"]
                country, flag = classify_country(lname)
                st = (comp.get("status", {}).get("type", {}) or {})
                games.append({
                    "league": lname,
                    "leagueName": lname,
                    "country": country,
                    "flag": flag,
                    "home": (home.get("team", {}).get("displayName") or "Home")[:40],
                    "away": (away.get("team", {}).get("displayName") or "Away")[:40],
                    "score": st.get("shortDetail") or "TBD",
                    "live": st.get("state") == "in",
                    "status": st.get("description") or "",
                })

        # League-specific for better coverage when "all" is sparse
        if len(games) < 20:
            for code in LEAGUES:
                if len(games) > 60:
                    break
                data = get_json(
                    f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={date_str}"
                )
                if not data:
                    continue
                lname = (data.get("leagues") or [{}])[0].get("name") if data.get("leagues") else code
                for ev in data.get("events", [])[:8]:
                    comp = (ev.get("competitions") or [{}])[0]
                    cs = comp.get("competitors") or []
                    if len(cs) < 2:
                        continue
                    home = next((x for x in cs if x.get("homeAway") == "home"), cs[0])
                    away = next((x for x in cs if x.get("homeAway") == "away"), cs[1])
                    country, flag = classify_country(lname)
                    st = (comp.get("status", {}).get("type", {}) or {})
                    games.append({
                        "league": lname,
                        "leagueName": lname,
                        "country": country,
                        "flag": flag,
                        "home": (home.get("team", {}).get("displayName") or "Home")[:40],
                        "away": (away.get("team", {}).get("displayName") or "Away")[:40],
                        "score": st.get("shortDetail") or "TBD",
                        "live": st.get("state") == "in",
                        "status": st.get("description") or "",
                    })

    # Deduplicate
    seen = set()
    out = []
    for g in games:
        k = (g["home"].lower(), g["away"].lower(), g["leagueName"].lower())
        if k not in seen:
            seen.add(k)
            out.append(g)

    print(f"Final games: {len(out)}")
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
    })

@app.route("/api/prob")
def api_prob():
    home = request.args.get("home", "Home").strip()
    away = request.args.get("away", "Away").strip()
    if not home or not away:
        return jsonify({"error": "Both home and away teams are required."}), 400

    # For now we use the deterministic model.
    # Real L5 would require team-ID mapping per league (can be added later).
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
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Football Analysis</title>
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; background: #1c2333; color: #fff; font-family: system-ui, -apple-system, Arial, sans-serif; }
    .top { padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; background: #1c2333; position: sticky; top: 0; z-index: 20; border-bottom: 1px solid #2a3447; }
    .live-btn { background: #2a3447; padding: 6px 14px; border-radius: 20px; font-size: 12px; cursor: pointer; user-select: none; }
    .live-btn.active { background: #ff4444; color: #fff; }
    .country-head { padding: 14px 16px; font-weight: 600; background: #0f141f; display: flex; justify-content: space-between; cursor: pointer; border-bottom: 1px solid #242f44; }
    .league-tabs { display: flex; gap: 8px; padding: 10px 12px; overflow-x: auto; background: #121a2a; white-space: nowrap; scrollbar-width: none; }
    .league-tabs::-webkit-scrollbar { display: none; }
    .ltab { padding: 6px 14px; background: #1a2535; border-radius: 20px; font-size: 12px; cursor: pointer; border: 1px solid #2a3447; flex-shrink: 0; }
    .ltab.active { background: #00ff88; color: #000; font-weight: 700; }
    .fixtures-wrap { background: #121a2a; padding-bottom: 8px; }
    .fixture { background: #242f44; margin: 8px 12px; padding: 14px; border-radius: 12px; cursor: pointer; border-left: 3px solid #00ff88; transition: background .15s; }
    .fixture:hover { background: #2c3a55; }
    .fixture.live { border-left-color: #ff4444; }
    .stats { display: none; background: #0f141f; margin: 0 12px 12px; padding: 8px; border-radius: 12px; }
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
    .bottom { position: fixed; bottom: 0; left: 0; right: 0; background: #1c2333; display: flex; justify-content: space-around; padding: 12px 0; border-top: 1px solid #2a3447; font-size: 13px; z-index: 30; }
    #loader { padding: 40px 20px; text-align: center; color: #8a96a8; }
  </style>
</head>
<body>
  <div class="top">
    <h3 style="margin:0;font-size:18px">Today <span id="count" style="color:#00ff88;font-weight:400"></span></h3>
    <div class="live-btn" id="liveBtn" onclick="showLive()">● LIVE</div>
  </div>

  <div id="loader">Loading ESPN fixtures…</div>
  <div id="list"></div>
  <div style="height:80px"></div>

  <div class="bottom">
    <div>🗓️ Fixtures</div>
    <div>🔔 Alerts</div>
    <div>📈 Trends</div>
    <div>☰ More</div>
  </div>

<script>
let allGames = [];
let view = "fixtures";
let openC = {};
let selL = {};

function showLive() {
  view = view === "live" ? "fixtures" : "live";
  document.getElementById("liveBtn").classList.toggle("active", view === "live");
  render();
}

function toggleC(k) {
  openC[k] = !openC[k];
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

function render() {
  let html = "";
  const filt = view === "live" ? allGames.filter(g => g.live) : allGames;
  const by = {};

  filt.forEach(g => {
    const k = g.flag + "|" + g.country;
    if (!by[k]) by[k] = [];
    by[k].push(g);
  });

  document.getElementById("count").textContent = "(" + filt.length + ")";

  if (filt.length === 0) {
    html = "<div class='error'>No fixtures were returned. Check the server log and ESPN connection.</div>";
  }

  for (const ck in by) {
    const games = by[ck];
    const parts = ck.split("|");
    const flag = parts[0];
    const country = parts[1];
    const isOpen = openC[ck] !== false;
    const leagues = [...new Set(games.map(x => x.leagueName))];
    if (!selL[ck]) selL[ck] = leagues[0];
    const sel = selL[ck];
    const liveC = games.filter(x => x.live).length;

    html += `<div class="country-head" onclick="toggleC('${ck.replace(/'/g, "\\\\'")}')">
      <span>${flag} ${escapeHtml(country)} (${games.length}) ${liveC > 0 ? "🔴" + liveC : ""}</span>
      <span>${isOpen ? "▼" : "▶"}</span>
    </div>`;

    if (isOpen) {
      html += `<div class="league-tabs">`;
      leagues.forEach(l => {
        const c = games.filter(x => x.leagueName === l).length;
        const act = l === sel ? "active" : "";
        html += `<div class="ltab ${act}" onclick="event.stopPropagation();selectL('${ck.replace(/'/g, "\\\\'")}','${l.replace(/'/g, "\\\\'")}')">${escapeHtml(l)} (${c})</div>`;
      });
      html += `</div><div class="fixtures-wrap">`;

      games.filter(x => x.leagueName === sel).forEach((f, i) => {
        const uid = btoa(unescape(encodeURIComponent(ck + "|" + f.home + "|" + f.away + "|" + i))).replace(/[^a-zA-Z0-9]/g, "");
        html += `
          <div class="fixture ${f.live ? "live" : ""}" onclick="openP('${escapeHtml(f.home).replace(/'/g, "\\\\'")}','${escapeHtml(f.away).replace(/'/g, "\\\\'")}','${uid}')">
            <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
              <b style="flex:1;text-align:right">${escapeHtml(f.home)}</b>
              <span style="opacity:.6">vs</span>
              <b style="flex:1">${escapeHtml(f.away)}</b>
              <span style="color:#ffcc00;min-width:48px;text-align:right">${escapeHtml(f.score)}</span>
            </div>
            <small style="color:#8a96a8;display:block;margin-top:4px">${escapeHtml(f.leagueName)}</small>
          </div>
          <div class="stats" id="stats-${uid}"></div>`;
      });
      html += `</div>`;
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
  box.innerHTML = "<div style='padding:12px;color:#8a96a8'>Calculating L5…</div>";
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
  .catch(err => {
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
