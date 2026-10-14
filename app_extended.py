"""
app_extended.py — IntruGuard
============================
Extended version of app.py that adds:
  1. CORS support (for React dev server on port 3000)
  2. /live-data  → JSON endpoint consumed by the React dashboard
  3. /logs       → JSON endpoint for raw log retrieval

HOW TO USE:
  Replace `python app.py` with `python app_extended.py`
  OR apply the diff manually to app.py (shown in README).

The original /  (dashboard) route is preserved unchanged.
The ML pipeline (flow_processor_2, sniffing thread) is untouched.
"""

import sqlite3
from threading import Thread
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from flow_processor_2 import start_sniffing
from config import DB_PATH
from log_monitor import start_log_monitor
app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow React dev server (localhost:3000) and production build (same origin).
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",   # Vite default fallback
            "http://127.0.0.1:5173",
        ]
    }
})

# ── DB HELPERS ────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            time   TEXT,
            src    TEXT,
            dst    TEXT,
            attack TEXT,
            action TEXT
        )
    """)
    conn.commit()
    conn.close()
    print(f"[+] Database initialised at: {DB_PATH}")


def get_logs(limit=50):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT time, src, dst, attack, action FROM logs ORDER BY time DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"time": r[0], "src": r[1], "dst": r[2], "attack": r[3], "action": r[4]}
            for r in rows]


# ── ORIGINAL ROUTE (unchanged) ────────────────────────────────────────────────
@app.route("/")
def dashboard():
    logs = get_logs()
    # Convert back to tuples so the original template works
    log_tuples = [(l["time"], l["src"], l["dst"], l["attack"], l["action"]) for l in logs]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("index.html", logs=log_tuples, now=now)


# ── NEW: /live-data ───────────────────────────────────────────────────────────
@app.route("/live-data")
def live_data():
    """
    Returns aggregated stats + recent logs + threat distribution.

    Response shape:
    {
      "stats": {
        "total":   <int>,
        "attacks": <int>,
        "benign":  <int>,
        "blocked": <int>
      },
      "logs": [
        { "time": "...", "src": "...", "dst": "...", "attack": "...", "action": "..." },
        ...
      ],
      "distribution": {
        "BENIGN":  <int>,
        "DoS":     <int>,
        ...
      },
      "timestamp": "2024-01-01T12:00:00"
    }
    """
    logs = get_logs(limit=50)

    total   = len(logs)
    attacks = sum(1 for l in logs if l["attack"] and l["attack"].upper() != "BENIGN")
    benign  = total - attacks
    blocked = sum(1 for l in logs if l["action"] == "Blocked")

    # Build threat distribution map
    distribution = {}
    for l in logs:
        label = l["attack"] or "UNKNOWN"
        distribution[label] = distribution.get(label, 0) + 1

    return jsonify({
        "stats": {
            "total":   total,
            "attacks": attacks,
            "benign":  benign,
            "blocked": blocked,
        },
        "logs": logs,
        "distribution": distribution,
        "timestamp": datetime.now().isoformat(),
    })


# ── NEW: /logs ────────────────────────────────────────────────────────────────
@app.route("/logs")
def api_logs():
    """
    Optional: raw log endpoint with ?limit= query param.
    """
    try:
        limit = int(request.args.get("limit", 50))
        limit = max(1, min(limit, 500))   # clamp between 1–500
    except (TypeError, ValueError):
        limit = 50

    logs = get_logs(limit=limit)
    return jsonify({"logs": logs, "count": len(logs)})


# ── STARTUP ───────────────────────────────────────────────────────────────────
def run_ids():
    start_sniffing()

# ── RUN LOG IDS ─────────────────────────────────────────────
def run_log_ids():
    start_log_monitor()

if __name__ == "__main__":
    init_db()

    t = Thread(target=run_ids)
    t.daemon = True
    t.start()
    t2 = Thread(target=run_log_ids)
    t2.daemon = True
    t2.start()

    app.run(host="0.0.0.0", port=5000, debug=False)
