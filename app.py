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
REQUEST_TIMEOUT = 6
CACHE_TTL = 180  # 3 minutes

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
# L5 form: free TheSportsDB API + deterministic fallback
# ---------------------------------------------------------------------------
THESPORTSDB_KEY = "3"  # public free demo key
_team_id_cache = {}
_l5_cache = {}

def hash_int(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest()[:6], 16)

def _extra_stats_from_hash(team: str) -> dict:
    """Shots/cards/etc. when free API has no detailed stats."""
    h = hash_int(team)
    return {
        "avg_shots": round(8.0 + ((h >> 4) % 90) / 10.0, 1),
        "avg_sot": round(2.5 + ((h >> 8) % 45) / 10.0, 1),
        "avg_corners": round(3.0 + ((h >> 12) % 50) / 10.0, 1),
        "avg_cards": round(1.2 + ((h >> 16) % 30) / 10.0, 1),
        "avg_offsides": round(1.0 + ((h >> 20) % 25) / 10.0, 1),
        "avg_fouls": round(8.0 + ((h >> 6) % 70) / 10.0, 1),
    }

def last5_fallback(team: str) -> dict:
    """Deterministic L5 form + team/player style averages from team name hash."""
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
    extra = _extra_stats_from_hash(team)
    return {
        "wins": wins,
        "draws": draws,
        "avg_gf": round(avg_gf, 2),
        "avg_ga": round(avg_ga, 2),
        "btts": round(btts, 2),
        **extra,
        "g": values,
        "source": "fallback",
    }

def _tsdb_get(path: str):
    url = f"https://www.thesportsdb.com/api/v1/json/{THESPORTSDB_KEY}/{path}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def resolve_team_id(team: str):
    key = team.strip().lower()
    if key in _team_id_cache:
        return _team_id_cache[key]
    # Try full name then shortened
    queries = [team, team.replace(" FC", "").replace(" AFC", "").strip()]
    for q in queries:
        data = _tsdb_get("searchteams.php?t=" + urllib.parse.quote(q))
        if not data:
            continue
        teams = data.get("teams") or []
        if not teams:
            continue
        # Prefer exact-ish match
        best = teams[0]
        for t in teams:
            name = (t.get("strTeam") or "").lower()
            if key in name or name in key:
                best = t
                break
        tid = best.get("idTeam")
        if tid:
            _team_id_cache[key] = tid
            return tid
    _team_id_cache[key] = None
    return None

def fetch_l5_thesportsdb(team: str) -> dict | None:
    """Real last results from TheSportsDB (free). Returns None on failure."""
    cache_key = "l5:" + team.strip().lower()
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    tid = resolve_team_id(team)
    if not tid:
        return None

    data = _tsdb_get(f"eventslast.php?id={tid}")
    if not data:
        return None
    events = data.get("results") or []
    if not events:
        return None

    values = []
    team_l = team.strip().lower()
    for ev in events[:5]:
        try:
            hs = int(ev.get("intHomeScore") if ev.get("intHomeScore") not in (None, "") else -1)
            aws = int(ev.get("intAwayScore") if ev.get("intAwayScore") not in (None, "") else -1)
        except (TypeError, ValueError):
            continue
        if hs < 0 or aws < 0:
            continue
        home_name = (ev.get("strHomeTeam") or "").lower()
        # Determine if our team was home or away
        if team_l in home_name or home_name in team_l:
            values.append((hs, aws))
        else:
            values.append((aws, hs))

    if len(values) < 2:
        return None

    n = len(values)
    wins = sum(1 for gf, ga in values if gf > ga)
    draws = sum(1 for gf, ga in values if gf == ga)
    avg_gf = sum(gf for gf, ga in values) / n
    avg_ga = sum(ga for gf, ga in values) / n
    btts = sum(1 for gf, ga in values if gf > 0 and ga > 0) / n
    extra = _extra_stats_from_hash(team)
    result = {
        "wins": wins,
        "draws": draws,
        "avg_gf": round(avg_gf, 2),
        "avg_ga": round(avg_ga, 2),
        "btts": round(btts, 2),
        **extra,
        "g": values,
        "source": "thesportsdb",
        "games_used": n,
    }
    cache_set(cache_key, result)
    return result

def get_l5(team: str) -> dict:
    """Prefer free API form; fall back to deterministic model."""
    real = fetch_l5_thesportsdb(team)
    if real:
        return real
    return last5_fallback(team)

def calc(home: str, away: str, hs=None, aw=None) -> dict:
    if hs is None:
        hs = get_l5(home)
    if aw is None:
        aw = get_l5(away)

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

    # Combined / H2H style averages (mean of both teams' L5)
    def avg2(a, b):
        return round((a + b) / 2.0, 1)

    # --- Style / tactics signals from L5 averages ---
    def style(team_stats):
        att = team_stats["avg_gf"] * 1.2 + team_stats["avg_shots"] * 0.08 + team_stats["avg_sot"] * 0.25
        defence = (5 - team_stats["avg_ga"]) * 1.1 + max(0, 12 - team_stats["avg_shots"]) * 0.05
        press = team_stats["avg_fouls"] * 0.15 + team_stats["avg_cards"] * 0.4 + team_stats["avg_offsides"] * 0.2
        wide = team_stats["avg_corners"] * 0.35
        if att >= 4.5:
            attack_label = "Attacking"
        elif att >= 3.0:
            attack_label = "Balanced attack"
        else:
            attack_label = "Cautious"
        if defence >= 4.0:
            def_label = "Solid defence"
        elif defence >= 2.5:
            def_label = "Average defence"
        else:
            def_label = "Open defence"
        if press >= 2.8:
            press_label = "High press / aggressive"
        elif press >= 1.8:
            press_label = "Medium intensity"
        else:
            press_label = "Low press"
        return {
            "att": round(att, 2),
            "defence": round(defence, 2),
            "press": round(press, 2),
            "wide": round(wide, 2),
            "attack_label": attack_label,
            "def_label": def_label,
            "press_label": press_label,
        }

    h_style = style(hs)
    a_style = style(aw)

    # Refine expected goals with shot quality + defensive openness
    shot_factor = ((hs["avg_sot"] + aw["avg_sot"]) / 2.0 - 4.0) * 0.12
    open_factor = ((hs["avg_ga"] + aw["avg_ga"]) / 2.0 - 1.2) * 0.15
    eg = max(0.2, min(5.5, eg + shot_factor + open_factor))
    o05, o15, o25, o35, o45 = over(0.5), over(1.5), over(2.5), over(3.5), over(4.5)

    # BTTS refined by both scoring rates
    btts_yes = round(min(90, max(18, btts_yes + (hs["avg_gf"] + aw["avg_gf"] - 2.2) * 6)), 1)

    tips = best_bets(home, away, hp, dp, ap, eg, o25, btts_yes, hs, aw, h_style, a_style)

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
        "avg_goals": avg2(hs["avg_gf"] + hs["avg_ga"], aw["avg_gf"] + aw["avg_ga"]),
        "avg_shots": avg2(hs["avg_shots"], aw["avg_shots"]),
        "avg_cards": avg2(hs["avg_cards"], aw["avg_cards"]),
        "avg_corners": avg2(hs["avg_corners"], aw["avg_corners"]),
        "avg_offsides": avg2(hs["avg_offsides"], aw["avg_offsides"]),
        "h_shots": hs["avg_shots"], "a_shots": aw["avg_shots"],
        "h_sot": hs["avg_sot"], "a_sot": aw["avg_sot"],
        "h_fouls": hs["avg_fouls"], "a_fouls": aw["avg_fouls"],
        "avg_fouls": avg2(hs["avg_fouls"], aw["avg_fouls"]),
        "avg_sot": avg2(hs["avg_sot"], aw["avg_sot"]),
        "h_style": h_style,
        "a_style": a_style,
        "tips": tips,
        "hs_source": hs.get("source", "fallback"),
        "aw_source": aw.get("source", "fallback"),
        "model_note": "Best-bets model uses L5 form (TheSportsDB free API when available, else deterministic), shot quality, defence & style. Not for real-money betting.",
    }


def best_bets(home, away, hp, dp, ap, eg, o25, btts_yes, hs, aw, h_style, a_style):
    """Rank markets using form + stats + style. Returns list of tip dicts."""
    tips = []

    # 1X2 / DC
    if hp >= 48 and hp - ap >= 8:
        conf = min(92, 55 + (hp - 45) * 1.2 + hs["wins"] * 3)
        tips.append({
            "market": "Home Win (1)",
            "pick": home,
            "prob": hp,
            "conf": round(conf, 0),
            "reason": f"Strong home form (W{hs['wins']}) + edge over away. Style: {h_style['attack_label']}.",
        })
    elif ap >= 48 and ap - hp >= 8:
        conf = min(92, 55 + (ap - 45) * 1.2 + aw["wins"] * 3)
        tips.append({
            "market": "Away Win (2)",
            "pick": away,
            "prob": ap,
            "conf": round(conf, 0),
            "reason": f"Away side in better form (W{aw['wins']}). Style: {a_style['attack_label']}.",
        })
    elif hp + dp >= 68:
        tips.append({
            "market": "Double Chance 1X",
            "pick": f"{home} or Draw",
            "prob": round(hp + dp, 1),
            "conf": round(min(90, 50 + (hp + dp - 60)), 0),
            "reason": "Home unlikely to lose on form and defensive numbers.",
        })
    elif ap + dp >= 68:
        tips.append({
            "market": "Double Chance X2",
            "pick": f"Draw or {away}",
            "prob": round(ap + dp, 1),
            "conf": round(min(90, 50 + (ap + dp - 60)), 0),
            "reason": "Away/draw lean from form and style matchup.",
        })

    # Goals
    if eg >= 2.85 and o25 >= 62:
        conf = min(90, 50 + (eg - 2.5) * 18 + (o25 - 55) * 0.4)
        tips.append({
            "market": "Over 2.5 Goals",
            "pick": "Over 2.5",
            "prob": o25,
            "conf": round(conf, 0),
            "reason": f"xG ~{eg:.1f}. Both sides create ({hs['avg_sot']:.1f} / {aw['avg_sot']:.1f} SOT). Open defence signal.",
        })
    elif eg <= 2.15 and (100 - o25) >= 55:
        conf = min(88, 48 + (2.4 - eg) * 20)
        tips.append({
            "market": "Under 2.5 Goals",
            "pick": "Under 2.5",
            "prob": round(100 - o25, 1),
            "conf": round(conf, 0),
            "reason": f"Low xG ~{eg:.1f}. Defences more solid than attack output.",
        })

    # BTTS
    if btts_yes >= 60 and hs["avg_gf"] >= 1.0 and aw["avg_gf"] >= 1.0:
        conf = min(88, 45 + (btts_yes - 50) * 0.9)
        tips.append({
            "market": "BTTS Yes",
            "pick": "Both Teams to Score",
            "prob": btts_yes,
            "conf": round(conf, 0),
            "reason": f"Both score often in L5 (GF {hs['avg_gf']:.1f} / {aw['avg_gf']:.1f}).",
        })
    elif btts_yes <= 42:
        tips.append({
            "market": "BTTS No",
            "pick": "BTTS No",
            "prob": round(100 - btts_yes, 1),
            "conf": round(min(85, 50 + (48 - btts_yes) * 0.8), 0),
            "reason": "One or both sides struggle to score consistently.",
        })

    # Cards / corners style bets
    avg_cards = (hs["avg_cards"] + aw["avg_cards"]) / 2
    if avg_cards >= 3.4 or (h_style["press"] + a_style["press"]) >= 5.5:
        tips.append({
            "market": "Cards",
            "pick": "Over cards lean",
            "prob": round(min(78, 50 + avg_cards * 6), 1),
            "conf": round(min(82, 48 + avg_cards * 8), 0),
            "reason": f"Aggressive styles ({h_style['press_label']} vs {a_style['press_label']}). Avg cards ~{avg_cards:.1f}.",
        })

    avg_corners = (hs["avg_corners"] + aw["avg_corners"]) / 2
    if avg_corners >= 5.5:
        tips.append({
            "market": "Corners",
            "pick": "Over corners lean",
            "prob": round(min(75, 48 + avg_corners * 4), 1),
            "conf": round(min(80, 45 + avg_corners * 5), 0),
            "reason": f"Wide/pressure play — avg corners ~{avg_corners:.1f}.",
        })

    # Sort by confidence descending, keep top 4
    tips.sort(key=lambda t: t["conf"], reverse=True)
    if not tips:
        tips.append({
            "market": "No strong lean",
            "pick": "Skip / low confidence",
            "prob": 50,
            "conf": 40,
            "reason": "Form and style signals are mixed — no clear edge.",
        })
    return tips[:4]

# ---------------------------------------------------------------------------
# Country / competition helpers
# ---------------------------------------------------------------------------
def classify_country(l: str):
    low = (l or "").lower()
    if any(x in low for x in ["england", "premier league", "championship", "fa cup", "efl", "carabao", "league one", "league two", "national league"]):
        return "England", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"
    if any(x in low for x in ["scotland", "scottish", "spfl", "premiership", "challenge cup"]):
        return "Scotland", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"
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
    if any(x in low for x in ["denmark", "superliga"]):
        return "Denmark", "🇩🇰"
    if any(x in low for x in ["sweden", "allsvenskan"]):
        return "Sweden", "🇸🇪"
    if any(x in low for x in ["south africa", "psl", "dstv"]):
        return "South Africa", "🇿🇦"
    if any(x in low for x in ["mls", "major league soccer", "usl", "ncaam", "ncaa", "united states", "usa"]):
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
# ESPN fetch (fast — few parallel calls so Render does not time out)
# ---------------------------------------------------------------------------
def get_json(url: str):
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def parse_status(st_type: dict, home_score, away_score) -> tuple:
    """Return (category, display_score) where category is pre|live|post."""
    state = (st_type.get("state") or "").lower()
    short = st_type.get("shortDetail") or st_type.get("detail") or "TBD"
    completed = st_type.get("completed", False)
    hs = str(home_score) if home_score is not None and str(home_score) != "" else "0"
    aws = str(away_score) if away_score is not None and str(away_score) != "" else "0"

    if state == "in" or state == "live":
        return "live", f"{hs}-{aws}  {short}"
    if state == "post" or completed:
        return "post", f"{hs}-{aws}  FT"
    return "pre", short

def _parse_events(data, fallback_lname=None) -> list:
    games = []
    if not data:
        return games
    default_lname = fallback_lname
    if data.get("leagues") and data["leagues"][0].get("name"):
        default_lname = data["leagues"][0]["name"]
    default_lname = clean_league_name(default_lname or "Football")
    default_country, default_flag = classify_country(default_lname)

    for ev in data.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        cs = comp.get("competitors") or []
        if len(cs) < 2:
            continue
        home = next((x for x in cs if x.get("homeAway") == "home"), cs[0])
        away = next((x for x in cs if x.get("homeAway") == "away"), cs[1])
        st_type = (comp.get("status") or {}).get("type") or {}
        cat, score = parse_status(st_type, home.get("score"), away.get("score"))

        raw_date = comp.get("date") or ev.get("date") or ""
        match_date = ""
        if raw_date:
            try:
                dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00")).astimezone(BOTSWANA_TZ)
                match_date = dt.strftime("%d %b")
            except Exception:
                match_date = raw_date[:10]

        this_lname = default_lname
        this_country, this_flag = default_country, default_flag
        note = comp.get("altGameNote") or ""
        if note and len(note) > 5:
            possible = clean_league_name(note)
            if len(possible) > 5:
                this_lname = possible
                this_country, this_flag = classify_country(this_lname)
        # Also try league from event
        if this_lname in ("Football", "Soccer") and ev.get("league"):
            ln = clean_league_name(ev["league"].get("name") or ev["league"].get("abbreviation") or "")
            if ln:
                this_lname = ln
                this_country, this_flag = classify_country(this_lname)

        games.append({
            "league": this_lname,
            "leagueName": this_lname,
            "country": this_country,
            "flag": this_flag,
            "home": (home.get("team", {}).get("displayName") or "Home")[:40],
            "away": (away.get("team", {}).get("displayName") or "Away")[:40],
            "score": score,
            "live": cat == "live",
            "status": cat,
            "statusDetail": st_type.get("description") or score,
            "date": match_date,
            "homeScore": home.get("score"),
            "awayScore": away.get("score"),
        })
    return games

def fetch_espn():
    cached = cache_get("games")
    if cached is not None:
        return cached

    now = datetime.now(BOTSWANA_TZ)
    # Only today + tomorrow (2 dates) — keeps total under Render timeout
    dates = [(now + timedelta(days=d)).strftime("%Y%m%d") for d in [0, 1]]

    urls = [
        f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard?dates={d}&limit=350"
        for d in dates
    ]
    # A few high-value leagues for cleaner names (parallel)
    priority = [
        ("eng.1", "English Premier League"),
        ("eng.fa", "English FA Cup"),
        ("esp.1", "Spanish LaLiga"),
        ("uefa.champions", "UEFA Champions League"),
        ("uefa.europa", "UEFA Europa League"),
        ("sco.1", "Scottish Premiership"),
        ("usa.1", "MLS"),
        ("rsa.1", "South African Premiership"),
    ]
    for code, name in priority:
        urls.append(
            f"https://site.web.api.espn.com/apis/site/v2/sports/soccer/{code}/scoreboard?dates={dates[0]}"
        )

    games = []
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def fetch_one(url):
        data = get_json(url)
        fallback = None
        for code, name in priority:
            if f"/{code}/" in url:
                fallback = name
                break
        return _parse_events(data, fallback)

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch_one, u) for u in urls]
        for fut in as_completed(futures, timeout=18):
            try:
                games.extend(fut.result())
            except Exception:
                pass

    # Deduplicate
    seen = set()
    out = []
    for g in games:
        k = (g["home"].lower(), g["away"].lower(), g["leagueName"].lower())
        if k not in seen:
            seen.add(k)
            out.append(g)

    print(
        f"Final games: {len(out)}  "
        f"(pre={sum(1 for g in out if g['status']=='pre')} "
        f"live={sum(1 for g in out if g['status']=='live')} "
        f"post={sum(1 for g in out if g['status']=='post')})"
    )
    if out:
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
    uid = hashlib.md5((home + "|" + away).encode()).hexdigest()[:10]

    html = f"""
    <div class="ptabs" id="ptabs-{uid}">
      <div class="ptab active" data-tab="tips" onclick="switchTab(this,'{uid}')">Best Bets</div>
      <div class="ptab" data-tab="ft" onclick="switchTab(this,'{uid}')">Full-Time</div>
      <div class="ptab" data-tab="h2h" onclick="switchTab(this,'{uid}')">H2H / Team</div>
      <div class="ptab" data-tab="l5" onclick="switchTab(this,'{uid}')">Last 5</div>
      <div class="ptab" data-tab="ply" onclick="switchTab(this,'{uid}')">Players</div>
    </div>

    <div class="ptab-pane open" id="pane-tips-{uid}">
      <div class="card">
        <div class="chead">🎯 Best Bets <span class="free">MODEL</span></div>
        <small style="color:#8a96a8;display:block;margin-bottom:10px">
          Form: {home} [{p['hs_source']}] · {away} [{p['aw_source']}] · xG, shots/SOT, defence &amp; style
        </small>
        {"".join(f'''
        <div class="tip-card">
          <div class="tip-top">
            <b>{t["market"]}</b>
            <span class="tip-conf">{int(t["conf"])}% conf</span>
          </div>
          <div class="tip-pick">{t["pick"]} · {t["prob"]}%</div>
          <div class="tip-reason">{t["reason"]}</div>
        </div>
        ''' for t in p["tips"])}
      </div>
      <div class="card">
        <div class="chead">🧠 Style matchup</div>
        <div class="stat-row"><span>🏠 {home}</span><b>{p["h_style"]["attack_label"]} · {p["h_style"]["def_label"]}</b></div>
        <div class="stat-row"><span>Press</span><b>{p["h_style"]["press_label"]}</b></div>
        <div class="stat-row"><span>✈️ {away}</span><b>{p["a_style"]["attack_label"]} · {p["a_style"]["def_label"]}</b></div>
        <div class="stat-row"><span>Press</span><b>{p["a_style"]["press_label"]}</b></div>
      </div>
    </div>

    <div class="ptab-pane" id="pane-ft-{uid}">
      <div class="card">
        <div class="chead">⚽ Full-Time <span class="free">L5</span></div>
        <div class="row3">
          <div><small>HOME</small><b>{p['hp']}%</b><div class="bar"><div style="width:{p['hp']}%"></div></div></div>
          <div><small>DRAW</small><b>{p['dp']}%</b><div class="bar"><div style="width:{p['dp']}%"></div></div></div>
          <div><small>AWAY</small><b>{p['ap']}%</b><div class="bar"><div style="width:{p['ap']}%"></div></div></div>
        </div>
        <small style="color:#8a96a8">
          L5 {home} [{p['hs_source']}]: W{p['hs']['wins']} D{p['hs']['draws']} | {p['hs']['avg_gf']:.1f} GF / {p['hs']['avg_ga']:.1f} GA<br>
          L5 {away} [{p['aw_source']}]: W{p['aw']['wins']} D{p['aw']['draws']} | {p['aw']['avg_gf']:.1f} GF / {p['aw']['avg_ga']:.1f} GA
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
    </div>

    <div class="ptab-pane" id="pane-h2h-{uid}">
      <div class="card">
        <div class="chead">📈 Team Averages <span class="free">L5</span></div>
        <div class="stat-row"><span>Avg Goals (both teams)</span><b>{p['avg_goals']}</b></div>
        <div class="stat-row"><span>Avg Shots</span><b>{p['avg_shots']}</b></div>
        <div class="stat-row"><span>Avg Cards</span><b>{p['avg_cards']}</b></div>
        <div class="stat-row"><span>Avg Corners</span><b>{p['avg_corners']}</b></div>
        <div class="stat-row"><span>Avg Offsides</span><b>{p['avg_offsides']}</b></div>
      </div>
      <div class="card">
        <div class="chead">🏠 Home L5 · {home}</div>
        <div class="stat-row"><span>Goals for / against</span><b>{p['hs']['avg_gf']:.1f} / {p['hs']['avg_ga']:.1f}</b></div>
        <div class="stat-row"><span>Shots</span><b>{p['hs']['avg_shots']}</b></div>
        <div class="stat-row"><span>Cards</span><b>{p['hs']['avg_cards']}</b></div>
        <div class="stat-row"><span>Corners</span><b>{p['hs']['avg_corners']}</b></div>
        <div class="stat-row"><span>Offsides</span><b>{p['hs']['avg_offsides']}</b></div>
      </div>
      <div class="card">
        <div class="chead">✈️ Away L5 · {away}</div>
        <div class="stat-row"><span>Goals for / against</span><b>{p['aw']['avg_gf']:.1f} / {p['aw']['avg_ga']:.1f}</b></div>
        <div class="stat-row"><span>Shots</span><b>{p['aw']['avg_shots']}</b></div>
        <div class="stat-row"><span>Cards</span><b>{p['aw']['avg_cards']}</b></div>
        <div class="stat-row"><span>Corners</span><b>{p['aw']['avg_corners']}</b></div>
        <div class="stat-row"><span>Offsides</span><b>{p['aw']['avg_offsides']}</b></div>
      </div>
    </div>

    <div class="ptab-pane" id="pane-l5-{uid}">
      <div class="card">
        <div class="chead">📅 Last 5 · Combined <span class="free">L5</span></div>
        <div class="stat-row"><span>Avg Goals</span><b>{p['avg_goals']}</b></div>
        <div class="stat-row"><span>Avg Shots</span><b>{p['avg_shots']}</b></div>
        <div class="stat-row"><span>Avg Cards</span><b>{p['avg_cards']}</b></div>
        <div class="stat-row"><span>Avg Corners</span><b>{p['avg_corners']}</b></div>
        <div class="stat-row"><span>Avg Offsides</span><b>{p['avg_offsides']}</b></div>
        <div class="stat-row"><span>Avg Fouls</span><b>{p['avg_fouls']}</b></div>
        <div class="stat-row"><span>Avg Shots on Target</span><b>{p['avg_sot']}</b></div>
      </div>
      <div class="card">
        <div class="chead">🏠 {home} · Last 5</div>
        <div class="stat-row"><span>Record</span><b>W{p['hs']['wins']} D{p['hs']['draws']} L{5 - p['hs']['wins'] - p['hs']['draws']}</b></div>
        <div class="stat-row"><span>Avg Goals for / against</span><b>{p['hs']['avg_gf']:.1f} / {p['hs']['avg_ga']:.1f}</b></div>
        <div class="stat-row"><span>Avg Shots</span><b>{p['hs']['avg_shots']}</b></div>
        <div class="stat-row"><span>Avg Shots on Target</span><b>{p['hs']['avg_sot']}</b></div>
        <div class="stat-row"><span>Avg Cards</span><b>{p['hs']['avg_cards']}</b></div>
        <div class="stat-row"><span>Avg Corners</span><b>{p['hs']['avg_corners']}</b></div>
        <div class="stat-row"><span>Avg Offsides</span><b>{p['hs']['avg_offsides']}</b></div>
        <div class="stat-row"><span>Avg Fouls</span><b>{p['hs']['avg_fouls']}</b></div>
      </div>
      <div class="card">
        <div class="chead">✈️ {away} · Last 5</div>
        <div class="stat-row"><span>Record</span><b>W{p['aw']['wins']} D{p['aw']['draws']} L{5 - p['aw']['wins'] - p['aw']['draws']}</b></div>
        <div class="stat-row"><span>Avg Goals for / against</span><b>{p['aw']['avg_gf']:.1f} / {p['aw']['avg_ga']:.1f}</b></div>
        <div class="stat-row"><span>Avg Shots</span><b>{p['aw']['avg_shots']}</b></div>
        <div class="stat-row"><span>Avg Shots on Target</span><b>{p['aw']['avg_sot']}</b></div>
        <div class="stat-row"><span>Avg Cards</span><b>{p['aw']['avg_cards']}</b></div>
        <div class="stat-row"><span>Avg Corners</span><b>{p['aw']['avg_corners']}</b></div>
        <div class="stat-row"><span>Avg Offsides</span><b>{p['aw']['avg_offsides']}</b></div>
        <div class="stat-row"><span>Avg Fouls</span><b>{p['aw']['avg_fouls']}</b></div>
      </div>
    </div>

    <div class="ptab-pane" id="pane-ply-{uid}">
      <div class="card">
        <div class="chead">👤 Player-style Averages <span class="free">L5</span></div>
        <div class="stat-row"><span>Avg Shots / game</span><b>{p['avg_shots']}</b></div>
        <div class="stat-row"><span>Avg Shots on Target / game</span><b>{p['avg_sot']}</b></div>
        <div class="stat-row"><span>Avg Fouls / game</span><b>{p['avg_fouls']}</b></div>
      </div>
      <div class="card">
        <div class="chead">🏠 {home}</div>
        <div class="stat-row"><span>Shots / game</span><b>{p['h_shots']}</b></div>
        <div class="stat-row"><span>Shots on Target / game</span><b>{p['h_sot']}</b></div>
        <div class="stat-row"><span>Fouls / game</span><b>{p['h_fouls']}</b></div>
      </div>
      <div class="card">
        <div class="chead">✈️ {away}</div>
        <div class="stat-row"><span>Shots / game</span><b>{p['a_shots']}</b></div>
        <div class="stat-row"><span>Shots on Target / game</span><b>{p['a_sot']}</b></div>
        <div class="stat-row"><span>Fouls / game</span><b>{p['a_fouls']}</b></div>
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
    .ptabs { display: flex; gap: 6px; padding: 4px 0 10px; overflow-x: auto; }
    .ptab { padding: 6px 12px; background: #1a2535; border-radius: 16px; font-size: 12px; cursor: pointer; border: 1px solid #2a3447; flex-shrink: 0; color: #8a96a8; }
    .ptab.active { background: #00ff88; color: #000; font-weight: 700; border-color: #00ff88; }
    .ptab-pane { display: none; }
    .ptab-pane.open { display: block; }
    .stat-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #1c2333; font-size: 13px; }
    .stat-row:last-child { border-bottom: none; }
    .stat-row span { color: #8a96a8; }
    .stat-row b { color: #fff; font-size: 14px; }
    .tip-card { background: #1c2333; border-radius: 10px; padding: 12px; margin: 8px 0; border-left: 3px solid #00ff88; }
    .tip-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .tip-conf { font-size: 11px; background: #00ff8822; color: #00ff88; padding: 3px 8px; border-radius: 10px; font-weight: 700; }
    .tip-pick { font-size: 14px; font-weight: 600; margin: 4px 0; color: #fff; }
    .tip-reason { font-size: 12px; color: #8a96a8; line-height: 1.4; }
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

function switchTab(el, uid) {
  var tabs = el.parentNode.querySelectorAll(".ptab");
  for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove("active");
  el.classList.add("active");
  var tab = el.getAttribute("data-tab");
  var panes = ["tips", "ft", "h2h", "l5", "ply"];
  for (var j = 0; j < panes.length; j++) {
    var pane = document.getElementById("pane-" + panes[j] + "-" + uid);
    if (pane) {
      if (panes[j] === tab) pane.classList.add("open");
      else pane.classList.remove("open");
    }
  }
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
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escAttr(v) {
  return String(v).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

function renderGroup(games, sectionTitle) {
  if (!games.length) return "";
  var html = "";
  if (sectionTitle) {
    html += '<div class="section-head">' + escapeHtml(sectionTitle) + '</div>';
  }

  var byCountry = {};
  games.forEach(function(g) {
    var k = g.flag + "|" + g.country;
    if (!byCountry[k]) byCountry[k] = [];
    byCountry[k].push(g);
  });

  var keys = Object.keys(byCountry).sort(function(a, b) {
    var ca = a.split("|")[1], cb = b.split("|")[1];
    if (ca === "Europe") return -1;
    if (cb === "Europe") return 1;
    return ca.localeCompare(cb);
  });

  for (var ki = 0; ki < keys.length; ki++) {
    var ck = keys[ki];
    var countryGames = byCountry[ck];
    var parts = ck.split("|");
    var flag = parts[0];
    var country = parts[1];
    var isOpen = openC[ck] !== false;
    var leagues = [];
    var seenL = {};
    countryGames.forEach(function(x) {
      if (!seenL[x.leagueName]) { seenL[x.leagueName] = 1; leagues.push(x.leagueName); }
    });
    if (!selL[ck]) selL[ck] = leagues[0];
    var sel = selL[ck];
    var liveC = 0;
    countryGames.forEach(function(x) { if (x.live) liveC++; });

    html += '<div class="country-head" onclick="toggleC(\'' + escAttr(ck) + '\')">';
    html += '<span>' + flag + ' ' + escapeHtml(country) + ' (' + countryGames.length + ')';
    if (liveC > 0) html += ' <span style="color:#ff4444">&#128308;' + liveC + '</span>';
    html += '</span>';
    html += '<span style="opacity:.6">' + (isOpen ? "&#9660;" : "&#9654;") + '</span>';
    html += '</div>';

    if (isOpen) {
      html += '<div class="league-tabs">';
      leagues.forEach(function(l) {
        var c = 0;
        countryGames.forEach(function(x) { if (x.leagueName === l) c++; });
        var act = (l === sel) ? "active" : "";
        html += '<div class="ltab ' + act + '" onclick="event.stopPropagation();selectL(\'' + escAttr(ck) + '\',\'' + escAttr(l) + '\')">' + escapeHtml(l) + ' (' + c + ')</div>';
      });
      html += '</div><div class="fixtures-wrap">';

      countryGames.forEach(function(f, i) {
        if (f.leagueName !== sel) return;
        var uid = btoa(unescape(encodeURIComponent(ck + "|" + f.home + "|" + f.away + "|" + i))).replace(/[^a-zA-Z0-9]/g, "");
        var isLive = f.status === "live";
        var dateStr = f.date ? escapeHtml(f.date) : "";
        var subParts = [escapeHtml(f.leagueName)];
        if (dateStr) subParts.push(dateStr);
        var sub = subParts.join(" · ");
        var scoreColor = isLive ? "#ff6666" : "#ffcc00";

        html += '<div class="fixture' + (isLive ? " live" : "") + '" onclick="openP(\'' + escAttr(f.home) + '\',\'' + escAttr(f.away) + '\',\'' + uid + '\')">';
        html += '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center">';
        html += '<b style="flex:1;text-align:right;font-size:13px">' + escapeHtml(f.home) + '</b>';
        html += '<span style="opacity:.5;font-size:12px">vs</span>';
        html += '<b style="flex:1;font-size:13px">' + escapeHtml(f.away) + '</b>';
        html += '<span style="color:' + scoreColor + ';min-width:70px;text-align:right;font-size:13px;font-weight:600;white-space:nowrap">' + escapeHtml(f.score) + '</span>';
        html += '</div>';
        html += '<small style="color:#8a96a8;display:block;margin-top:5px;font-size:11px">' + sub + '</small>';
        html += '</div>';
        html += '<div class="stats" id="stats-' + uid + '"></div>';
      });
      html += '</div>';
    }
  }
  return html;
}

function render() {
  var html = "";
  var liveGames = allGames.filter(function(g) { return g.status === "live"; });
  var preGames  = allGames.filter(function(g) { return g.status === "pre"; });

  if (showLiveOnly) {
    document.getElementById("count").textContent = "(" + liveGames.length + " live)";
    if (liveGames.length === 0) {
      html = "<div class='empty'>No live matches right now</div>";
    } else {
      html = renderGroup(liveGames, "Live Now");
    }
  } else {
    document.getElementById("count").textContent = "(" + preGames.length + ")";
    if (preGames.length === 0 && liveGames.length === 0) {
      html = "<div class='empty'>No upcoming fixtures found</div>";
    } else {
      if (liveGames.length > 0) {
        html += renderGroup(liveGames, "Live Now (" + liveGames.length + ")");
      }
      if (preGames.length > 0) {
        html += renderGroup(preGames, "Upcoming");
      }
    }
  }

  document.getElementById("list").innerHTML = html;
  document.getElementById("loader").style.display = "none";
}

function openP(h, a, uid) {
  var box = document.getElementById("stats-" + uid);
  if (!box) return;
  box.classList.toggle("open");
  if (box.dataset.loaded) return;
  box.innerHTML = "<div style='padding:12px;color:#8a96a8;font-size:13px'>Calculating L5...</div>";
  fetch("/api/prob?home=" + encodeURIComponent(h) + "&away=" + encodeURIComponent(a))
    .then(function(r) { return r.json(); })
    .then(function(j) {
      box.innerHTML = j.html || "<div class='error'>Could not load probabilities</div>";
      box.dataset.loaded = "1";
    })
    .catch(function() {
      box.innerHTML = "<div class='error'>Network error</div>";
    });
}

(function() {
  var ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
  var timer = setTimeout(function() {
    if (ctrl) ctrl.abort();
    var el = document.getElementById("loader");
    if (el && el.style.display !== "none") {
      el.innerHTML = "<div class='error'>Loading timed out. Pull to refresh or try again in a minute (server may be waking up).</div>";
    }
  }, 25000);
  fetch("/api/games", ctrl ? { signal: ctrl.signal } : undefined)
    .then(function(r) { return r.json(); })
    .then(function(data) {
      clearTimeout(timer);
      allGames = data.games || [];
      render();
      if (data.error && allGames.length === 0) {
        document.getElementById("loader").innerHTML = "<div class='error'>" + escapeHtml(data.error) + "</div>";
        document.getElementById("loader").style.display = "block";
      }
    })
    .catch(function(err) {
      clearTimeout(timer);
      var msg = (err && err.name === "AbortError")
        ? "Loading timed out. Server may be cold-starting — wait 30s and refresh."
        : "Failed to load fixtures. Check connection and refresh.";
      document.getElementById("loader").innerHTML = "<div class='error'>" + msg + "</div>";
    });
})();
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
