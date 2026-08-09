#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA = "bie.strat365.series-readiness.v0"

def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def gp(obj, name, default=None):
    return obj.get(name, default) if isinstance(obj, dict) else default

def normalize_bases(value):
    raw = value if isinstance(value, list) else ([] if not value else [value])
    out = []
    for item in raw:
        text = str(item).strip()
        if text in {"1","2","3"}:
            out.append(int(text))
    return sorted(set(out))

def state_key(outs, bases):
    try:
        outs = int(outs)
    except Exception:
        return None
    if outs not in (0,1,2):
        return None
    return "outs={}|bases={}".format(outs, "".join(str(x) for x in bases) if bases else "empty")

def parse_runs(text):
    text = "" if text is None else str(text)
    return len(re.findall(r"(?:^|\s)(?:[123]|b)-H(?:\s|$)", text))

def classify_tactical(rec):
    result = str(gp(rec,"result","") or "").lower()
    roll = str(gp(rec,"roll","") or "").lower()
    tags = []
    if "sac bunt" in result or roll == "sac": tags.append("bunt")
    if "sac fly" in result: tags.append("sac_fly")
    if "stolen base" in result: tags.append("stolen_base")
    if "caught stealing" in result: tags.append("caught_stealing")
    if roll == "h&r": tags.append("hit_and_run")
    if "wild pitch" in result: tags.append("wild_pitch")
    if "passed ball" in result: tags.append("passed_ball")
    if "int walk" in result: tags.append("intentional_walk")
    if "error" in result: tags.append("error")
    if "double play" in result: tags.append("double_play")
    return tags

def catastrophic(result, bases):
    low = (result or "").lower()
    return bool(
        "double play" in low or
        "caught stealing" in low or
        ("strike out" in low and bool(bases))
    )

def mechanism(rec, runs):
    if runs <= 0:
        return None
    low = str(gp(rec,"result","") or "").lower()
    if "home run" in low: return "home_run"
    if "triple" in low or "double" in low: return "extra_base_hit"
    if "single" in low: return "single"
    if "sac fly" in low: return "sac_fly"
    if "ground out" in low or "force play" in low or "fielders choice" in low or "fielder's choice" in low:
        return "productive_out"
    if "error" in low: return "error_aided"
    if "wild pitch" in low or "passed ball" in low: return "misc_advancement"
    return "other"

def sides(game, half):
    home = gp(gp(game,"homeTeam",{}),"name","")
    away = gp(gp(game,"awayTeam",{}),"name","")
    if str(half).upper() == "BOTTOM": return home, away
    if str(half).upper() == "TOP": return away, home
    return None, None

def analyze_game(game, team_name):
    records = list(gp(gp(game,"playByPlay",{}),"orderedRecords",[]) or [])
    home = gp(gp(game,"homeTeam",{}),"name","")
    away = gp(gp(game,"awayTeam",{}),"name","")
    if team_name not in {home,away}:
        raise ValueError("team missing from game")

    rows = []
    for rec in records:
        if gp(rec,"recordType","") != "EVENT":
            continue
        offense, defense = sides(game, gp(rec,"half",""))
        bases = normalize_bases(gp(rec,"occupiedBasesBefore",[]))
        rows.append({
            "inning": str(gp(rec,"inning","") or ""),
            "half": str(gp(rec,"half","") or "").upper(),
            "offense": offense,
            "defense": defense,
            "outs": gp(rec,"outsBefore",None),
            "bases": bases,
            "state": state_key(gp(rec,"outsBefore",None), bases),
            "result": str(gp(rec,"result","") or ""),
            "runs": parse_runs(gp(rec,"baserunners","")),
            "tags": classify_tactical(rec),
            "rec": rec,
        })

    offense_states = defaultdict(lambda: {"opportunities":0,"converted":0,"runs_to_inning_end":0})
    defense_states = defaultdict(lambda: {"opportunities":0,"prevented":0,"runs_to_inning_end":0})
    two_out = {"opportunities":0,"converted":0,"runs_to_inning_end":0}
    cats = Counter()
    tactics = Counter()
    mechs = Counter()
    errors = Counter()

    for i,row in enumerate(rows):
        if row["state"] is None:
            continue
        future_runs = 0
        for later in rows[i:]:
            if later["inning"] != row["inning"] or later["half"] != row["half"]:
                break
            future_runs += later["runs"]

        if row["offense"] == team_name:
            b = offense_states[row["state"]]
            b["opportunities"] += 1
            b["runs_to_inning_end"] += future_runs
            if future_runs > 0: b["converted"] += 1
            try:
                outs = int(row["outs"])
            except Exception:
                outs = None
            if outs == 2 and row["bases"]:
                two_out["opportunities"] += 1
                two_out["runs_to_inning_end"] += future_runs
                if future_runs > 0: two_out["converted"] += 1
            if catastrophic(row["result"], row["bases"]):
                cats[row["result"]] += 1
            for tag in row["tags"]:
                tactics[tag] += 1
            m = mechanism(row["rec"], row["runs"])
            if m: mechs[m] += row["runs"]

        if row["defense"] == team_name:
            b = defense_states[row["state"]]
            b["opportunities"] += 1
            b["runs_to_inning_end"] += future_runs
            if future_runs == 0: b["prevented"] += 1
            if "error" in row["result"].lower():
                errors[row["result"]] += 1

    return {
        "homeTeam":home,
        "awayTeam":away,
        "eventCount":len(rows),
        "offenseStatePerformance":dict(sorted(offense_states.items())),
        "defenseStatePerformance":dict(sorted(defense_states.items())),
        "twoOutConversion":two_out,
        "catastrophicOutcomes":dict(cats),
        "tacticalEvents":dict(tactics),
        "runMechanisms":dict(mechs),
        "defenseErrorEvents":dict(errors),
    }

def aggregate(games):
    off = defaultdict(lambda: {"opportunities":0,"converted":0,"runs_to_inning_end":0})
    deff = defaultdict(lambda: {"opportunities":0,"prevented":0,"runs_to_inning_end":0})
    two = {"opportunities":0,"converted":0,"runs_to_inning_end":0}
    cats = Counter(); tactics = Counter(); mechs = Counter(); errors = Counter()

    for g in games:
        for s,d in g["offenseStatePerformance"].items():
            for k in off[s]: off[s][k] += int(d.get(k,0))
        for s,d in g["defenseStatePerformance"].items():
            for k in deff[s]: deff[s][k] += int(d.get(k,0))
        for k in two: two[k] += int(g["twoOutConversion"].get(k,0))
        cats.update(g["catastrophicOutcomes"])
        tactics.update(g["tacticalEvents"])
        mechs.update(g["runMechanisms"])
        errors.update(g["defenseErrorEvents"])

    off_rows = []
    for s,d in sorted(off.items()):
        row = dict(d); row["state"] = s
        row["conversionRate"] = round(d["converted"]/d["opportunities"],4) if d["opportunities"] else None
        off_rows.append(row)

    def_rows = []
    for s,d in sorted(deff.items()):
        row = dict(d); row["state"] = s
        row["preventionRate"] = round(d["prevented"]/d["opportunities"],4) if d["opportunities"] else None
        def_rows.append(row)

    two["conversionRate"] = round(two["converted"]/two["opportunities"],4) if two["opportunities"] else None

    return {
        "offenseBaseOutStates":off_rows,
        "defenseBaseOutStates":def_rows,
        "twoOutConversion":two,
        "catastrophicOutcomes":dict(cats),
        "tacticalEvents":dict(tactics),
        "runMechanisms":dict(mechs),
        "winMechanismDiversityCount":len([1 for v in mechs.values() if v > 0]),
        "defenseErrorEvents":dict(errors),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parsed-root",required=True)
    ap.add_argument("--team-name",required=True)
    ap.add_argument("--league-id",required=True)
    ap.add_argument("--league-date",required=True)
    ap.add_argument("--output",required=True)
    a = ap.parse_args()

    root = Path(a.parsed_root)
    paths = sorted((root/"games").glob("game-*-v0.json"))
    if len(paths) != 3:
        raise SystemExit("Expected exactly 3 parsed games; found {}".format(len(paths)))

    games = []
    ids = []
    for p in paths:
        m = re.match(r"game-(\d+)-v0\.json$",p.name)
        if not m:
            continue
        ids.append(m.group(1))
        g = analyze_game(load_json(p),a.team_name)
        g["gameId"] = m.group(1)
        games.append(g)

    out = {
        "schema":SCHEMA,
        "season":1968,
        "leagueId":str(a.league_id),
        "leagueDate":str(a.league_date),
        "teamName":a.team_name,
        "sourceParsedRoot":str(root),
        "gameIds":ids,
        "gameCount":len(games),
        "seriesReadinessSignals":aggregate(games),
        "games":games,
        "notes":[
            "v0 measures realized inning-end conversion from each observed base/out state.",
            "v0 separates offensive state conversion from defensive state prevention.",
            "v0 records tactical and catastrophic outcomes as observed events rather than assuming value.",
            "v0 records defensive error events separately so pitching review can distinguish defense-created leverage.",
            "v0 win-mechanism diversity is a simple count of distinct run-scoring mechanism classes observed in the series.",
            "v0 does not yet calculate empirical run expectancy, leverage index, handedness splits, park adjustment, or player-card balance."
        ]
    }

    op = Path(a.output)
    op.parent.mkdir(parents=True,exist_ok=True)
    with op.open("w",encoding="utf-8",newline="\n") as f:
        json.dump(out,f,indent=2,sort_keys=True)
        f.write("\n")

if __name__ == "__main__":
    main()