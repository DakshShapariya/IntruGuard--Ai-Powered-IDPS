import sqlite3
from threading import Thread
from datetime import datetime
from flask import Flask, render_template
from flow_processor_2 import start_sniffing
# [P7] Shared paths/features live in config.py.
from config import DB_PATH

app = Flask(__name__)

# -------- DB INIT — once at startup --------
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

# -------- FETCH LOGS --------
def get_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY time DESC LIMIT 50")
    data = cursor.fetchall()
    conn.close()
    return data

# -------- DASHBOARD --------
@app.route("/")
def dashboard():
    logs = get_logs()
    now  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template("index.html", logs=logs, now=now)

# -------- RUN IDS --------
def run_ids():
    start_sniffing()

if __name__ == "__main__":
    init_db()

    t = Thread(target=run_ids)
    t.daemon = True
    t.start()

    app.run(host="0.0.0.0", port=5000, debug=False)
