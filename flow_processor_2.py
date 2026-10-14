import os
import time
import sqlite3
import ipaddress
import subprocess
import joblib
import pandas as pd
from datetime import datetime
from collections import Counter
from threading import Lock
from scapy.all import sniff, IP, TCP, UDP

# -------- PATHS --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database.db")

def model_path(name):
    return os.path.join(BASE_DIR, "models", name)

# -------- LOAD MODELS --------
rf     = joblib.load(model_path("rf.pkl"))
lr     = joblib.load(model_path("lr.pkl"))
xgb    = joblib.load(model_path("xgb.pkl"))
scaler = joblib.load(model_path("scaler.pkl"))
le     = joblib.load(model_path("le.pkl"))

print("[+] Models loaded:", list(le.classes_))

# -------- CONFIG --------
WINDOW_SECONDS = 2
BURST_PKT_THRESHOLD = 80

# -------- FEATURES --------
FEATURES = [
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Flow Packets/s",
    "Flow Bytes/s",
    "Average Packet Size",
    "FIN Flag Count",
    "ACK Flag Count",
    "PSH Flag Count",
    "RST Flag Count"
]

# -------- FLOW STORAGE --------
flows = {}
flows_lock = Lock()

# -------- DDoS AGGREGATION --------
target_stats = {}
TARGET_WINDOW = 1
DDOS_THRESHOLD = 200

# -------- NEW FLOW --------
def _new_flow():
    return {
        "start": time.time(),
        "fwd": 0,
        "bwd": 0,
        "bytes_fwd": 0,
        "bytes_bwd": 0,
        "fin": 0,
        "ack": 0,
        "psh": 0,
        "rst": 0,
    }

# -------- FEATURE EXTRACTION --------
def extract_features(flow):
    duration_us = (time.time() - flow["start"]) * 1_000_000
    duration_us = max(duration_us, 1.0)

    total_pkts  = flow["fwd"] + flow["bwd"]
    total_bytes = flow["bytes_fwd"] + flow["bytes_bwd"]
    duration_s  = duration_us / 1_000_000

    return [
        duration_us,
        flow["fwd"],
        flow["bwd"],
        flow["bytes_fwd"],
        flow["bytes_bwd"],
        total_pkts / duration_s,
        total_bytes / duration_s,
        total_bytes / (total_pkts + 1),
        flow["fin"],
        flow["ack"],
        flow["psh"],
        flow["rst"],
    ]

# -------- ML ENSEMBLE --------
def ensemble_predict(X_scaled):
    p1 = rf.predict(X_scaled)[0]
    p2 = lr.predict(X_scaled)[0]
    p3 = xgb.predict(X_scaled)[0]
    final = Counter([p1, p2, p3]).most_common(1)[0][0]
    return le.inverse_transform([final])[0]

# -------- RULE ENGINE --------
def rule_based_detection(features):
    (
        duration,
        fwd_pkts,
        bwd_pkts,
        fwd_bytes,
        bwd_bytes,
        pkt_rate,
        byte_rate,
        avg_pkt_size,
        fin,
        ack,
        psh,
        rst
    ) = features

    # -------- STRONG RULES --------

    if pkt_rate > 1000 and avg_pkt_size < 100 and rst > 10:
        return "SYN-Flood"

    if pkt_rate > 500 and avg_pkt_size > 500 and ack == 0 and psh == 0:
        return "UDP-Flood"

    if pkt_rate > 200 and bwd_bytes > fwd_bytes and avg_pkt_size > 400:
        return "DDoS"

    if fwd_pkts <= 2 and bwd_pkts <= 1 and pkt_rate < 50:
        return "PortScan"

    # -------- WEAK HEURISTICS --------

    if fwd_pkts > 10 and avg_pkt_size < 200:
        return "FTP-Patator"

    if fwd_pkts > 10 and avg_pkt_size < 200:
        return "SSH-Patator"

    if avg_pkt_size < 300 and pkt_rate > 50:
        return "Web Attack"

    return None

# -------- BLOCK --------
blocked_ips = set()

def prevent_attack(ip, attack):
    # Allow normal traffic
    if attack == "BENIGN":
        return "Allowed"

    # Validate IP
    try:
        ipaddress.IPv4Address(ip)
    except:
        return "Invalid IP"

    # Avoid duplicate blocking
    if ip in blocked_ips:
        return "Already Blocked"

    try:
        # Check if rule already exists
        check_cmd = [
            "iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"
        ]

        result = subprocess.run(
            check_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        if result.returncode != 0:
            # Add rule only if not exists
            subprocess.run(
                ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
                check=True
            )
            blocked_ips.add(ip)
            print(f" [BLOCKED] {ip}")

        return "Blocked"

    except Exception as e:
        print(f"[ERROR] iptables: {e}")
        return "Error"

# -------- LOG --------
def log_to_db(src, dst, attack, action):
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute(
        "INSERT INTO logs VALUES (?, ?, ?, ?, ?)",
        (str(datetime.now()), src, dst, attack, action)
    )
    conn.commit()
    conn.close()

# -------- CLASSIFY FLOW --------
def classify_flow(key):
    flow = flows[key]
    total_pkts = flow["fwd"] + flow["bwd"]

    if total_pkts < 5:
        return

    src, dst = key
    features = extract_features(flow)

    # DEBUG FEATURES
    print("\n[DEBUG FEATURES]")
    for n, v in zip(FEATURES, features):
        print(f"{n:30s}: {v}")

    X_df = pd.DataFrame([features], columns=FEATURES)
    X_scaled = scaler.transform(X_df)

    # -------- ML --------
    ml_pred = ensemble_predict(X_scaled)

    # -------- RULE --------
    rule_pred = rule_based_detection(features)

    # -------- VOLUME DDoS --------
    is_ddos_volume = (
        dst in target_stats and
        target_stats[dst]["count"] > DDOS_THRESHOLD
    )

    # -------- HYBRID DECISION --------
    if is_ddos_volume:
        final_pred = "DDoS"

    elif rule_pred in ["SYN-Flood", "UDP-Flood", "DDoS", "PortScan"]:
        final_pred = rule_pred

    elif rule_pred in ["FTP-Patator", "SSH-Patator", "Web Attack"]:
        if ml_pred == rule_pred:
            final_pred = rule_pred
        else:
            final_pred = ml_pred

    else:
        final_pred = ml_pred

    # DEBUG OUTPUT
    print("\n==============================")
    print(f"[ML]     : {ml_pred}")
    print(f"[RULE]   : {rule_pred}")
    print(f"[VOLUME] : {is_ddos_volume}")
    print(f"[FINAL]  : {final_pred}")
    print("==============================\n")

    action = prevent_attack(src, final_pred)
    log_to_db(src, dst, final_pred, action)

    flows[key] = _new_flow()

# -------- PACKET HANDLER --------
def process_packet(pkt):
    if IP not in pkt:
        return

    src = pkt[IP].src
    dst = pkt[IP].dst
    size = len(pkt)

    # -------- DDoS AGGREGATION --------
    now = time.time()
    if dst not in target_stats:
        target_stats[dst] = {"count": 0, "start": now}

    target_stats[dst]["count"] += 1
    elapsed = now - target_stats[dst]["start"]

    if elapsed <= TARGET_WINDOW and target_stats[dst]["count"] > DDOS_THRESHOLD:
        print(f"\n🚨 [DDoS ALERT] Target {dst} ({target_stats[dst]['count']} pkts/sec)\n")

    if elapsed > TARGET_WINDOW:
        target_stats[dst] = {"count": 0, "start": now}

    # -------- FLOW TRACKING --------
    with flows_lock:
        fwd_key = (src, dst)
        bwd_key = (dst, src)

        if fwd_key in flows:
            key, direction = fwd_key, "fwd"
        elif bwd_key in flows:
            key, direction = bwd_key, "bwd"
        else:
            flows[fwd_key] = _new_flow()
            key, direction = fwd_key, "fwd"

        flow = flows[key]

        if direction == "fwd":
            flow["fwd"] += 1
            flow["bytes_fwd"] += size
        else:
            flow["bwd"] += 1
            flow["bytes_bwd"] += size

        if TCP in pkt:
            f = pkt[TCP].flags
            if f & 0x01: flow["fin"] += 1
            if f & 0x10: flow["ack"] += 1
            if f & 0x08: flow["psh"] += 1
            if f & 0x04: flow["rst"] += 1

        total_pkts = flow["fwd"] + flow["bwd"]
        elapsed_secs = time.time() - flow["start"]

        if (
            (elapsed_secs >= WINDOW_SECONDS and total_pkts >= 5) or
            (total_pkts >= BURST_PKT_THRESHOLD)
        ):
            classify_flow(key)

# -------- START --------
def start_sniffing():
    print("[*] IDS started — capturing IP traffic...")
    sniff(
        filter="ip",
        prn=process_packet,
        store=0
    )
