"""
train_model.py — IntruGuard
======================================================
CORE FIX FOR ALWAYS-BENIGN ON LIVE DDoS:

The CIC-IDS-2017 DDoS is HTTP/UDP amplification (large packets,
~820 byte avg, high bwd bytes). A real hping3 SYN flood sends
54-byte SYN packets with no ACK/PSH and near-zero bwd bytes —
a completely different profile that the model never saw in training.

This script adds a synthetic "SYN-Flood" class built from the
statistical profile of hping3/scapy SYN floods so live attacks
are correctly classified.
======================================================
"""

import os
import numpy as np
import pandas as pd
import joblib
from collections import Counter
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

try:
    from imblearn.over_sampling import SMOTE
    USE_SMOTE = True
except ImportError:
    print("[!] imbalanced-learn not found — pip install imbalanced-learn --break-system-packages")
    USE_SMOTE = False

# [P7] Paths and FEATURES list are now imported from config.py so train and
#      inference can never disagree on column order.
from config import MODELS_DIR, CSV_PATH, FEATURES, model_path
os.makedirs(MODELS_DIR, exist_ok=True)

# ======================================================
# 1. LOAD + CLEAN DATASET
# ======================================================
print("[*] Loading CIC-IDS-2017 dataset...")
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
df["Label"] = df["Label"].str.strip()
df = df.dropna(subset=FEATURES + ["Label"])
df[FEATURES] = df[FEATURES].replace([np.inf, -np.inf], np.nan)
df = df.dropna(subset=FEATURES)

print(f"[*] Dataset shape: {df.shape}")
print("[*] Label distribution:")
for label, count in df["Label"].value_counts().items():
    print(f"      {label:20s}: {count:6d}  ({count/len(df)*100:.1f}%)")
print()

# ======================================================
# 2. INJECT SYNTHETIC SYN-FLOOD CLASS
#    Realistic profile: hping3 -S --flood against a Linux host whose kernel
#    replies RST,ACK to every SYN on a closed port. The previous version
#    assumed the target was a black hole (Total Bwd Pkts 0–8, ACK=0, RST=0–1,
#    Total Length of Fwd Pkts 40–120 bytes regardless of pkt count) which
#    didn't match real demo traffic, so live floods landed near BENIGN.
#
#    New signature:
#      • lots of small (~54 B) packets in BOTH directions
#      • bwd ≈ fwd (one RST,ACK per incoming SYN)
#      • ACK count ≈ bwd  (every RST,ACK has the ACK bit set)
#      • RST count ≈ bwd  (every RST,ACK has the RST bit set)
#      • FIN, PSH = 0
#      • all per-flow features derived from the SAME (n_fwd, n_bwd, avg_pkt,
#        duration) vector so they stay internally consistent.
# ======================================================
print("[*] Injecting synthetic SYN-Flood class...")
np.random.seed(42)
N_SYN = 8000   # enough to be a proper class, not too large to dominate

n_fwd = np.random.randint(50, 5000, N_SYN).astype(float)

#  MIX OF RESPONSE + NO-RESPONSE ATTACKS
mask = np.random.rand(N_SYN) < 0.5  # 50% cases

n_bwd = np.where(
    mask,
    n_fwd * np.random.uniform(0.7, 1.0, N_SYN),  # target replies (RST/ACK)
    0                                            # no response (pure SYN flood)
).astype(float)

avg_pkt = np.random.uniform(54, 66, N_SYN)
duration_us = np.random.uniform(200_000, 5_000_000, N_SYN)

syn_flood = pd.DataFrame({
    "Flow Duration":               duration_us,
    "Total Fwd Packets":           n_fwd,
    "Total Backward Packets":      n_bwd,
    "Total Length of Fwd Packets": n_fwd * avg_pkt,                   # was 40–120 (wrong)
    "Total Length of Bwd Packets": n_bwd * avg_pkt,                   # was 0–300 (wrong)
    "Flow Packets/s":              (n_fwd + n_bwd) / (duration_us / 1_000_000),
    "Flow Bytes/s":                (n_fwd + n_bwd) * avg_pkt / (duration_us / 1_000_000),
    "Average Packet Size":         avg_pkt,
    "FIN Flag Count":              np.zeros(N_SYN),
    "ACK Flag Count":              np.where(mask, n_bwd, 0),                              # one ACK per RST,ACK reply
    "PSH Flag Count":              np.zeros(N_SYN),
    "RST Flag Count":              np.where(mask, n_bwd, 0),                              # one RST per RST,ACK reply
})
syn_flood["Label"] = "SYN-Flood"

# [P4] UDP-Flood profile — hping3 --udp --flood: large random payloads, no
#      TCP flags. Kept in training because the sniffer now captures UDP
#      (BPF widened to `ip and (tcp or udp)` and process_packet falls
#      through cleanly for UDP — TCP flag counters stay at 0, matching
#      how this synthetic class is generated).
N_UDP = 5000
udp_flood = pd.DataFrame({
    "Flow Duration":               np.random.uniform(100_000, 10_000_000, N_UDP),
    "Total Fwd Packets":           np.random.randint(5, 500, N_UDP).astype(float),
    "Total Backward Packets":      np.random.randint(0, 5, N_UDP).astype(float),
    "Total Length of Fwd Packets": np.random.randint(500, 5000, N_UDP).astype(float),
    "Total Length of Bwd Packets": np.random.randint(0, 100, N_UDP).astype(float),
    "Flow Packets/s":              np.random.uniform(500, 100_000, N_UDP),
    "Flow Bytes/s":                np.random.uniform(500_000, 50_000_000, N_UDP),
    "Average Packet Size":         np.random.uniform(500, 1500, N_UDP),
    "FIN Flag Count":              np.zeros(N_UDP),
    "ACK Flag Count":              np.zeros(N_UDP),
    "PSH Flag Count":              np.zeros(N_UDP),
    "RST Flag Count":              np.zeros(N_UDP),
})
udp_flood["Label"] = "UDP-Flood"

df = pd.concat([df[FEATURES + ["Label"]], syn_flood, udp_flood], ignore_index=True)
df = df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

print(f"[*] Dataset after injection: {df.shape}")
print("[*] Updated label distribution:")
for label, count in df["Label"].value_counts().items():
    print(f"      {label:20s}: {count:6d}  ({count/len(df)*100:.1f}%)")
print()

X = df[FEATURES]
y = df["Label"].values

# ======================================================
# 3. ENCODE LABELS
# ======================================================
le = LabelEncoder()
y_encoded = le.fit_transform(y)
print(f"[*] All classes: {list(le.classes_)}")
print()

# ======================================================
# 4. TRAIN / TEST SPLIT
# ======================================================
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded,
    test_size=0.2,
    stratify=y_encoded,
    random_state=42
)
print(f"[*] Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")
print()

# ======================================================
# 5. SCALE
# ======================================================
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# ======================================================
# 6. SMOTE
# ======================================================
if USE_SMOTE:
    print("[*] Applying SMOTE...")
    print(f"    Before: {sorted(Counter(y_train).items())}")
    min_samples = min(Counter(y_train).values())
    k = max(1, min(5, min_samples - 1))
    smote = SMOTE(random_state=42, k_neighbors=k)
    X_train_scaled, y_train = smote.fit_resample(X_train_scaled, y_train)
    print(f"    After : {sorted(Counter(y_train).items())}")
    print()
else:
    print("[*] SMOTE skipped — class_weight='balanced' only.\n")

# ======================================================
# 7. TRAIN
# ======================================================

# Random Forest
print("[*] Training Random Forest...")
rf = RandomForestClassifier(
    n_estimators=200,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
    max_depth=20
)
rf.fit(X_train_scaled, y_train)
rf_preds = rf.predict(X_test_scaled)
print("[+] Random Forest:")
print(classification_report(y_test, rf_preds, target_names=le.classes_, zero_division=0))

# Logistic Regression
print("[*] Training Logistic Regression...")
lr = LogisticRegression(
    max_iter=2000,
    class_weight="balanced",
    random_state=42,
    solver="lbfgs"
)
lr.fit(X_train_scaled, y_train)
lr_preds = lr.predict(X_test_scaled)
print("[+] Logistic Regression:")
print(classification_report(y_test, lr_preds, target_names=le.classes_, zero_division=0))

# XGBoost
print("[*] Training XGBoost...")
sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)
xgb_clf = XGBClassifier(
    n_estimators=200,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
    max_depth=8,
    learning_rate=0.1,
)
xgb_clf.fit(X_train_scaled, y_train, sample_weight=sample_weights)
xgb_preds = xgb_clf.predict(X_test_scaled)
print("[+] XGBoost:")
print(classification_report(y_test, xgb_preds, target_names=le.classes_, zero_division=0))

# Ensemble
def majority_vote(p1, p2, p3):
    return np.array([Counter([a,b,c]).most_common(1)[0][0] for a,b,c in zip(p1,p2,p3)])

ens_preds = majority_vote(rf_preds, lr_preds, xgb_preds)
print("[+] Ensemble (Majority Vote):")
print(classification_report(y_test, ens_preds, target_names=le.classes_, zero_division=0))

# Feature importances
print("[*] RF Feature Importances:")
for feat, imp in sorted(zip(FEATURES, rf.feature_importances_), key=lambda x: -x[1]):
    print(f"    {feat:40s}: {imp:.4f}  {'█' * int(imp*50)}")
print()

# ======================================================
# 8. SAVE
# ======================================================
print("[*] Saving models...")
joblib.dump(rf,      model_path("rf.pkl"))
joblib.dump(lr,      model_path("lr.pkl"))
joblib.dump(xgb_clf, model_path("xgb.pkl"))
joblib.dump(scaler,  model_path("scaler.pkl"))
joblib.dump(le,      model_path("le.pkl"))

# [P6] Dropped the IsolationForest "compatibility stub" — flow_processor stopped
#      loading it after the architectural change to direct ensemble voting.
#      Saved ~15s of training time and ~840 KB of disk per retrain.

print(f"[+] All models saved → {MODELS_DIR}")
print()
print("=" * 55)
print("  Classes the model now knows:")
for c in le.classes_:
    print(f"    • {c}")
print()
print("  Run: sudo python3 app.py")
print("=" * 55)
