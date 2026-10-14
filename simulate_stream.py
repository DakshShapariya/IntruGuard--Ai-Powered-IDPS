"""
simulate_stream.py — IntruGuard Dev Tool
=========================================
Inserts synthetic log entries into the database so you can develop / demo
the React dashboard without needing root access or live network traffic.

Run this ALONGSIDE app_extended.py:
  Terminal 1:  python app_extended.py
  Terminal 2:  python simulate_stream.py

Stop with Ctrl+C.
"""

import sqlite3
import time
import random
from datetime import datetime
from config import DB_PATH

ATTACK_TYPES = [
    ("BENIGN",      0.55),
    ("DoS",         0.12),
    ("PortScan",    0.10),
    ("DDoS",        0.08),
    ("Brute Force", 0.06),
    ("Web Attack",  0.05),
    ("SYN-Flood",   0.02),
    ("UDP-Flood",   0.02),
]

ATTACK_WEIGHTS = [w for _, w in ATTACK_TYPES]
ATTACK_LABELS  = [l for l, _ in ATTACK_TYPES]


def random_ip():
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def insert_log(attack):
    action = "Blocked" if attack != "BENIGN" and random.random() > 0.3 else "Monitored"
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO logs (time, src, dst, attack, action) VALUES (?,?,?,?,?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            random_ip(),
            random_ip(),
            attack,
            action,
        )
    )
    conn.commit()
    conn.close()


def main():
    print("[simulate_stream] Starting synthetic traffic injection...")
    print("[simulate_stream] Press Ctrl+C to stop.\n")
    i = 0
    while True:
        attack = random.choices(ATTACK_LABELS, weights=ATTACK_WEIGHTS, k=1)[0]
        insert_log(attack)
        tag = "⚠ ATTACK" if attack != "BENIGN" else "  benign"
        print(f"[{i:04d}] {tag:10} → {attack}")
        i += 1
        time.sleep(random.uniform(0.8, 2.0))


if __name__ == "__main__":
    main()
