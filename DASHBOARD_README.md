# IntruGuard — React Dashboard Integration Guide

## What Was Added

```
Intruguard_updated/
├── app.py                    ← UNCHANGED (original Flask backend)
├── app_extended.py           ← NEW: app.py + CORS + /live-data + /logs
├── simulate_stream.py        ← NEW: dev tool to inject fake traffic
├── requirements_updated.txt  ← NEW: adds flask-cors
└── frontend/                 ← NEW: React dashboard
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── pages/
        │   └── Dashboard.jsx
        ├── components/
        │   ├── StatsCard.jsx
        │   ├── LiveChart.jsx
        │   ├── ThreatPieChart.jsx
        │   ├── LogsTable.jsx
        │   └── StatusIndicator.jsx
        └── services/
            └── api.js
```

---

## Step-by-Step Setup

### 1. Install Python dependency (flask-cors)

```bash
cd Intruguard_updated/
pip install flask-cors
# Kali/Debian:
pip install flask-cors --break-system-packages
```

### 2. Start the extended Flask backend

```bash
# From Intruguard_updated/
sudo python app_extended.py
```

> **Note:** `sudo` is needed because `flow_processor_2` uses `scapy` for live packet sniffing.  
> The original `app.py` is untouched — `app_extended.py` is a drop-in replacement.

### 3. (Optional) Start the traffic simulator for development

Open a second terminal:
```bash
cd Intruguard_updated/
python simulate_stream.py
```
This inserts synthetic attack/benign events into the database so the dashboard shows live data without needing real network traffic.

### 4. Install and run the React frontend

Open a third terminal:
```bash
cd Intruguard_updated/frontend/
npm install
npm run dev
```

Dashboard will be available at: **http://localhost:3000**

---

## API Endpoints Added

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Original Flask HTML dashboard (unchanged) |
| `GET` | `/live-data` | JSON: stats + logs + distribution |
| `GET` | `/logs?limit=N` | JSON: raw logs (default 50, max 500) |

### `/live-data` Response Shape

```json
{
  "stats": {
    "total": 42,
    "attacks": 8,
    "benign": 34,
    "blocked": 5
  },
  "logs": [
    {
      "time": "2024-01-15 10:30:45",
      "src": "192.168.1.100",
      "dst": "10.0.0.1",
      "attack": "DoS",
      "action": "Blocked"
    }
  ],
  "distribution": {
    "BENIGN": 34,
    "DoS": 5,
    "PortScan": 3
  },
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

---

## Dashboard Features

- **Live Stats Cards** — Total flows, Attacks, Benign, Blocked (auto-refresh every 1.5s)
- **Traffic Area Chart** — Rolling 60-point history of attacks vs benign traffic
- **Threat Pie Chart** — Distribution across all attack categories
- **Activity Log Table** — Last 10 events with colour-coded threat labels
- **Status Indicator** — Green (safe) / Red (attack) with live/offline badge

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Dashboard shows "Cannot reach backend" | Ensure `python app_extended.py` is running on port 5000 |
| CORS errors in browser console | Confirm you're using `app_extended.py`, not `app.py` |
| No data in charts | Run `python simulate_stream.py` to inject test data |
| npm not found | Install Node.js: `sudo apt install nodejs npm` |
| Port 3000 busy | Change `port: 3000` in `frontend/vite.config.js` |
