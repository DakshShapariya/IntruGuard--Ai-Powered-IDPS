"""
config.py — IntruGuard
======================
[P7] Single source of truth for paths and the feature vector.

Both `train_model.py` and `flow_processor.py` import from here so the column
order used at training time is guaranteed to match the column order used at
inference time. Without this, a silent reordering would scale the wrong values
with the wrong scaler weights and produce garbage predictions with no error.
"""

import os

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DB_PATH    = os.path.join(BASE_DIR, "database.db")
CSV_PATH   = os.path.join(BASE_DIR, "cicids.csv")

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
    "RST Flag Count",
]


def model_path(name: str) -> str:
    return os.path.join(MODELS_DIR, name)
