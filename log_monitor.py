import time
import re
import subprocess
import sqlite3
import ipaddress
from datetime import datetime
from collections import defaultdict
from threading import Lock

from config import DB_PATH
import subprocess

# -------- CONFIG --------
AUTH_LOG = "/var/log/auth.log"

SSH_THRESHOLD = 5
FTP_THRESHOLD = 5

blocked_ips = set()

ssh_attempts = defaultdict(int)
ftp_attempts = defaultdict(int)

db_lock = Lock()

# -------- DB LOG --------
def log_to_db(src, dst, attack, action):
    conn = sqlite3.connect(DB_PATH)

    with db_lock:
        conn.execute(
            "INSERT INTO logs VALUES (?, ?, ?, ?, ?)",
            (
                str(datetime.now()),
                src,
                dst,
                attack,
                action
            )
        )
        conn.commit()

    conn.close()

# -------- BLOCK IP --------
def block_ip(ip):
    if ip in blocked_ips:
        return "Already Blocked"

    try:
        ipaddress.IPv4Address(ip)
    except:
        return "Invalid IP"

    try:
        subprocess.run(
            ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
            check=True
        )

        blocked_ips.add(ip)

        print(f"\n[BLOCKED] {ip}\n")

        return "Blocked"

    except Exception as e:
        print(f"[ERROR] {e}")
        return "Error"

# -------- SSH DETECTION --------
def detect_ssh(line):
    if "Failed password" in line:
        match = re.search(
            r"from (\d+\.\d+\.\d+\.\d+)",
            line
        )

        if match:
            ip = match.group(1)

            ssh_attempts[ip] += 1

            print(f"[SSH FAIL] {ip} → {ssh_attempts[ip]}")

            if ssh_attempts[ip] >= SSH_THRESHOLD:

                print(f"\n🚨 SSH BRUTE FORCE: {ip}\n")

                action = block_ip(ip)

                log_to_db(
                    ip,
                    "LOCAL_SYSTEM",
                    "SSH-Patator",
                    action
                )

# -------- FTP DETECTION --------
def detect_ftp(line):
    if "authentication failure" in line.lower():

        match = re.search(
            r"rhost=(\d+\.\d+\.\d+\.\d+)",
            line
        )

        if match:
            ip = match.group(1)

            ftp_attempts[ip] += 1

            print(f"[FTP FAIL] {ip} → {ftp_attempts[ip]}")

            if ftp_attempts[ip] >= FTP_THRESHOLD:

                print(f"\n🚨 FTP BRUTE FORCE: {ip}\n")

                action = block_ip(ip)

                log_to_db(
                    ip,
                    "LOCAL_SYSTEM",
                    "FTP-Patator",
                    action
                )

# -------- MONITOR --------
def start_log_monitor():

    print("[*] Monitoring auth logs via journalctl...")

    process = subprocess.Popen(
        ["journalctl", "-f"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    while True:

        line = process.stdout.readline()

        if not line:
            continue

        detect_ssh(line)
        detect_ftp(line)
