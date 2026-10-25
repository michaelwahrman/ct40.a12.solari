#!/usr/bin/env python3
"""CT40.A12.Solari.make_schedule.py

Generates CT40.A12.Solari.schedule.json: the column labels plus an explicit,
time-stamped list of "row R shows these field values from time T" events.

You can hand-edit the JSON directly instead; this script is only a convenient
way to produce a believable day of Penn Station departures, spread from about
10 AM to midnight (trains arrive, board, depart, get delayed, change gates, and
the board ripples up when a train leaves).

Run (Linux / WSL):   python3 CT40.A12.Solari.make_schedule.py
Then:                python3 CT40.A12.Solari.build_embedded.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROWS = 10
START = "9:55:00 AM"
END = "6:30:00 PM"           # loop back to the morning while the board is still full (later trains are shown, not run)
STATION = "NEW YORK"
def secs(s):
    """'10:01 AM' or '9:58:05 AM' -> seconds after midnight."""
    t, ap = s.strip().split()
    parts = [int(p) for p in t.split(":")]
    while len(parts) < 3:
        parts.append(0)
    h, m, sec = parts
    h = h % 12 + (12 if ap.upper() == "PM" else 0)
    return h * 3600 + m * 60 + sec

def clock(n, with_seconds=True):
    n = int(round(n)) % 86400
    h, m, s = n // 3600, (n // 60) % 60, n % 60
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d}:{s:02d} {ap}" if with_seconds else f"{h12}:{m:02d} {ap}"

T0 = secs(START)

# A10: a departures board. Departure times are spread over the day (about every 35 min, 10 AM - midnight).
# name, origin, destination, scheduled departure from New York, gate.
# Trains that start elsewhere are "through" trains: they are ARRIVING, then ARRIVED, then BOARDING.
TRAINS = [
    ("NORTH CAROLINA SPECIAL",    "NEW YORK",    "RALEIGH",      "9:57 AM",  "7"),
    ("MERCHANTS LIMITED",         "BOSTON",      "WASHINGTON",   "10:32 AM", "12"),
    ("SILVER METEOR",             "NEW YORK",    "MIAMI",        "11:08 AM", "4"),
    ("CONGRESSIONAL",             "WASHINGTON",  "BOSTON",       "11:46 AM", "9"),
    ("LAKE SHORE LIMITED",        "NEW YORK",    "CHICAGO",      "12:25 PM", "15"),
    ("PALMETTO",                  "NEW YORK",    "SAVANNAH",     "1:03 PM",  "3"),
    ("MAPLE LEAF",                "NEW YORK",    "TORONTO",      "1:41 PM",  "11"),
    ("CRESCENT",                  "NEW YORK",    "NEW ORLEANS",  "2:17 PM",  "6"),
    ("YANKEE CLIPPER",            "BOSTON",      "PHILADELPHIA", "2:54 PM",  "13"),
    ("BROADWAY LIMITED",          "NEW YORK",    "CHICAGO",      "3:30 PM",  "10"),
    ("PENNSYLVANIAN",             "NEW YORK",    "PITTSBURGH",   "4:12 PM",  "2"),
    ("ADIRONDACK",                "NEW YORK",    "MONTREAL",     "4:45 PM",  "14"),
    ("SPIRIT OF ST. LOUIS",       "NEW YORK",    "ST. LOUIS",    "5:20 PM",  "5"),
    ("CAROLINIAN",                "NEW YORK",    "CHARLOTTE",    "5:58 PM",  "8"),
    ("SENATOR",                   "BOSTON",      "WASHINGTON",   "6:33 PM",  "12"),
    ("TWENTIETH CENTURY LIMITED", "NEW YORK",    "CHICAGO",      "7:10 PM",  "1"),
    ("VERMONTER",                 "WASHINGTON",  "ST. ALBANS",   "7:42 PM",  "16"),
    ("SOUTHERNER",                "NEW YORK",    "NEW ORLEANS",  "8:19 PM",  "4"),
    ("GEORGE WASHINGTON",         "NEW YORK",    "RICHMOND",     "8:55 PM",  "9"),
    ("FLORIDA SPECIAL",           "NEW YORK",    "TAMPA",        "9:31 PM",  "7"),
    ("ETHAN ALLEN EXPRESS",       "NEW YORK",    "RUTLAND",      "10:08 PM", "11"),
    ("CARDINAL",                  "NEW YORK",    "CINCINNATI",   "10:44 PM", "3"),
    ("NIGHT OWL",                 "BOSTON",      "WASHINGTON",   "11:20 PM", "12"),
    ("FEDERAL",                   "WASHINGTON",  "BOSTON",       "11:52 PM", "9"),
]

# Scripted surprises. dt is seconds after START; the first few land within
# seconds of the start "just for fun", the rest are spread through the day.
SURPRISES = [
    (4,     "NORTH CAROLINA SPECIAL", {"status": "DELAYED", "time": "10:01 AM"}),
    (9,     "PALMETTO",               {"gate": "17"}),
    (14,    "MAPLE LEAF",             {"status": "DELAYED", "time": "1:55 PM"}),
    (20,    "CRESCENT",               {"gate": "2"}),
    (27,    "YANKEE CLIPPER",         {"status": "CANCELLED"}),
    (35,    "BROADWAY LIMITED",       {"status": "DELAYED", "time": "3:45 PM"}),
    (1500,  "SILVER METEOR",          {"gate": "8"}),
    (3900,  "LAKE SHORE LIMITED",     {"status": "DELAYED", "time": "12:40 PM"}),
    (9000,  "ADIRONDACK",             {"gate": "18"}),
    (13200, "SPIRIT OF ST. LOUIS",    {"status": "DELAYED", "time": "5:36 PM"}),
    (18000, "SENATOR",                {"gate": "6"}),
    (22500, "VERMONTER",              {"status": "DELAYED", "time": "8:02 PM"}),
    (27000, "FLORIDA SPECIAL",        {"gate": "15"}),
    (33000, "NIGHT OWL",              {"status": "DELAYED", "time": "11:41 PM"}),
]

def build_timelines():
    """For each train: list of (t, changes) and a removal time."""
    tl = {}
    for name, frm, to, sched, gate in TRAINS:
        tl[name] = {
            "through": frm != STATION, "sort": secs(sched),
            "base": {"train": name, "from": frm, "to": to, "time": sched, "gate": gate, "status": "ON TIME"},
            "changes": [], "remove": None,
        }
    for dt, name, ch in SURPRISES:
        tl[name]["changes"].append((T0 + dt, dict(ch)))

    for name, t in tl.items():
        cancel = [w for w, ch in t["changes"] if ch.get("status") == "CANCELLED"]
        if cancel:
            t["remove"] = cancel[0] + 150
            continue
        eff = t["sort"]                         # departure time actually used (after any delay)
        for _, ch in t["changes"]:
            if "time" in ch:
                eff = secs(ch["time"])
        steps = []
        if t["through"]:
            steps += [(eff - 720, "ARRIVING"), (eff - 480, "ARRIVED")]
        steps += [(eff - 420, "BOARDING"), (eff - 60, "ALL ABOARD"), (eff, "DEPARTED")]
        t["remove"] = eff + 120
        delay_at = min([w for w, ch in t["changes"] if ch.get("status") == "DELAYED"], default=None)
        for when, st in steps:
            if delay_at is not None and when < delay_at and when > T0:
                continue                         # superseded by the delay announcement
            t["changes"].append((max(when, T0), {"status": st}))
        t["changes"].sort(key=lambda c: c[0])
    return tl

def state_at(tl, now):
    rows = []
    for name, t in tl.items():
        if t["remove"] is not None and now >= t["remove"]:
            continue
        cur = dict(t["base"])
        for when, ch in t["changes"]:
            if when <= now:
                cur.update(ch)
        rows.append((t["sort"], cur))
    rows.sort(key=lambda r: r[0])
    out = [r[1] for r in rows[:ROWS]]
    blank = {k: "" for k in ("train", "status", "from", "to", "time", "gate")}
    while len(out) < ROWS:
        out.append(dict(blank))
    return out

def main():
    tl = build_timelines()
    t_end = secs(END)
    times = {T0}
    for t in tl.values():
        for when, _ in t["changes"]:
            times.add(when)
        if t["remove"] is not None:
            times.add(t["remove"])
    times = sorted(x for x in times if T0 <= x < t_end)

    events, prev = [], None
    for now in times:
        cur = state_at(tl, now)
        for r, row in enumerate(cur):
            if prev is None:
                events.append({"t": clock(now), "row": r, "set": row})
            else:
                diff = {k: v for k, v in row.items() if prev[r].get(k) != v}
                if diff:
                    events.append({"t": clock(now), "row": r, "set": diff})
        prev = cur

    doc = {
        "_about": "CT40.A12.Solari schedule. 'labels' are the column headings shown above the board (one per field id in CT40.A12.Solari.fields.json). 'events' say: from master-clock time t, row 'row' (0 = top) shows these field values. Fields not mentioned keep what they had. The board state at any time = all events with t <= clock, applied in order. Times are h:mm:ss AM/PM. When the clock reaches endTime and loop is true, it jumps back to startTime.",
        "version": "CT40.A12.Solari",
        "title": "DEPARTURES",
        "labels": {"train": "TRAIN", "status": "STATUS", "from": "FROM",
                   "to": "TO", "time": "DEPARTURE TIME", "gate": "GATE"},
        "startTime": START,
        "endTime": END,
        "loop": True,
        "events": events,
    }
    path = os.path.join(HERE, "CT40.A12.Solari.schedule.json")
    with open(path, "w") as f:
        # one event per line keeps the file easy to read and hand-edit
        f.write("{\n")
        keys = [k for k in doc if k != "events"]
        for k in keys:
            f.write(f"  {json.dumps(k)}: {json.dumps(doc[k])},\n")
        f.write('  "events": [\n')
        f.write(",\n".join("    " + json.dumps(e) for e in events))
        f.write("\n  ]\n}\n")
    print(f"wrote {path}: {len(events)} events, {len(times)} change times")

if __name__ == "__main__":
    main()
