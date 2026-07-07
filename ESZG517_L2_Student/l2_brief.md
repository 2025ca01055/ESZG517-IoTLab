# ESZG517 — Lab Session L2
## Storage, Query & Visualisation
### Project 1 — Weather Station, Part 2

---

## What you need before the session

| Item | Source |
|---|---|
| `iotlab_config.json` | Copy from your `ESZG517_L1_Demo` folder into this folder |
| Python packages | `pip install paho-mqtt influxdb-client` |
| Node-RED | `npm install -g --unsafe-perm node-red` then `node-red` |
| Node-RED InfluxDB plugin | Node-RED → ☰ → Manage palette → Install → `node-red-contrib-influxdb` |
| Grafana Cloud account | grafana.com → Create free account (free, no credit card) |
| Arduino libraries | PubSubClient by Nick O'Leary + ArduinoJson by Benoit Blanchon |

**Copy config file now:**
```bash
cp ~/Desktop/ESZG517_L1_Demo/iotlab_config.json ~/Desktop/ESZG517_L2_Student/
```

---

## Session Flow

### Part 0 — Git Setup (10 min)
See Git section below. Complete before Part 1.

### Part 1 — Python Path (40 min)
1. Run InfluxDB self-test first: `python3 l2_db_writer.py`
2. Then run subscriber: `python3 l2_subscriber.py`
3. Open a second terminal, run: `python3 l1_publisher_KEY.py` (from L1 folder)
4. Verify `[DATA]` and `[INFLUX] Written:` lines appear every 5 seconds

### Part 2 — Node-RED Path (40 min)
1. Stop Python subscriber (`Ctrl+C`)
2. Open `http://localhost:1880`
3. Import `l2_nodered_flow.json` → configure HiveMQ + InfluxDB nodes → Deploy
4. Check Debug sidebar for incoming payloads

### Part 3 — Grafana (10 min in-session, finish as assignment)
Build at least the temperature panel live. Complete remaining panels after.

---

## Sensor Split

| # | Field | Unit | Implemented by |
|---|---|---|---|
| 1 | `temperature` | °C | Demo |
| 2 | `humidity` | % | Demo |
| 3 | `pressure` | hPa | Demo |
| 4 | `co2` | ppm | Demo |
| 5 | `aqi` | index | Demo |
| 6 | `light_level` | lux | **Your assignment** |
| 7 | `wind_speed` | m/s | **Your assignment** |
| 8 | `rainfall` | mm | **Your assignment** |
| 9 | `battery_voltage` | V | **Your assignment** |
| 10 | `rssi` | dBm | **Your assignment** |

**Note on field names:** The emulator publishes `co2_ppm` — this is automatically normalised to `co2` in the skeleton code. Always use `co2` in InfluxDB writes and Grafana queries.

Assignment sensors (6–10) are not in the emulator payload yet. The skeleton code fills them with realistic simulated values — your job is to write them to InfluxDB and visualise them in Grafana.

---

## Grafana Setup

### Add InfluxDB as a data source
1. Grafana → ☰ → Connections → Add new connection → InfluxDB → Create a InfluxDB data source
2. Fill in:

| Field | Value |
|---|---|
| Query Language | **Flux** |
| URL | your InfluxDB URL (from `iotlab_config.json`) |
| Organization | your org (from `iotlab_config.json`) |
| Token | your token (from `iotlab_config.json`) |
| Default Bucket | `iotlab` |

3. Save & Test → should say "datasource is working"

**Note:** The InfluxDB web UI shows SQL only — this is a UI change only. The API still supports Flux. Grafana connects via the API and works correctly with Flux queries.

### Building a panel
1. Dashboards → New → New dashboard → Add visualization → select InfluxDB
2. Query editor → click **Code** → type (do not copy-paste — use straight quotes):

```
from(bucket: "iotlab")
  |> range(start: -30m)
  |> filter(fn: (r) => r._measurement == "weather_station")
  |> filter(fn: (r) => r._field == "FIELD_NAME")
```

Replace `FIELD_NAME` with the sensor field. Click **Run query**.

### Required panels (all 5 needed for full marks)

| Panel | Field | Visualisation | Settings |
|---|---|---|---|
| Temperature | `temperature` | Time series | Unit: °C |
| Humidity | `humidity` | Gauge | 0–100 %, green <60, yellow <80, red ≥80 |
| Pressure | `pressure` | Time series | Unit: hPa |
| CO₂ | `co2` | Stat | Unit: ppm, red threshold at 1000 |
| AQI | `aqi` | Gauge | green 0–50, yellow 51–100, red 101+ |

### Creative panels (minimum 2)
Any 2 sensors from your assignment set. Any visualisation — justify in written analysis.

### Dashboard settings
- Time range: Last 30 minutes | Auto-refresh: 10s
- Title: `ESZG517 Weather Station — [Your Full Name]`

---

## Git & GitHub

### One-time setup
```bash
git config --global user.name "Your Name"
git config --global user.email "your@bits-pilani.ac.in"
```

### Create your private repo
1. github.com → + → New repository → Name: `ESZG517-IoTLab` → Private → Create
2. Copy the HTTPS URL shown

### Push L1 + L2 files
```bash
cd ~/Desktop/ESZG517_L1_Demo

# First time only
git init
git add l1_publisher.py l1_arduino.ino iotlab_config.json l1_brief.md
git commit -m "L1: MQTT publisher"
git remote add origin https://github.com/yourname/ESZG517-IoTLab.git
git branch -M main
git push -u origin main

# Add L2 after the session
cp ~/Desktop/ESZG517_L2_Student/l2_*.py .
cp ~/Desktop/ESZG517_L2_Student/l2_nodered_flow.json .
cp ~/Desktop/ESZG517_L2_Student/l2_arduino.ino .
git add l2_subscriber.py l2_db_writer.py l2_nodered_flow.json l2_arduino.ino
git commit -m "L2: storage query and visualisation — [your student ID]"
git push origin main
```

**GitHub asks for password?** Use a Personal Access Token:
GitHub → avatar → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate → tick `repo` → copy token → use as password.

---

## Submission Checklist

| Item | Requirement |
|---|---|
| `l2_subscriber.py` | All 10 sensors handled, runs without error |
| `l2_db_writer.py` | All 10 sensors written, query_recent returns data |
| `l2_nodered_flow.json` | Exported from Node-RED, all 10 sensors wired |
| `l2_arduino.ino` | All 10 sensors parsed and printed to Serial Monitor |
| Grafana screenshot | 7+ panels visible with live data |
| Written analysis | 200–300 words (prompts below) |
| GitHub link | L1 and L2 files committed |

### Written Analysis Prompts
1. **Pipeline latency** — Estimate time from emulator to Grafana. Which stage is the bottleneck?
2. **Python vs Node-RED** — What does each offer that the other doesn't? When would you choose each in production?
3. **Flux vs SQL** — How is `from() |> range() |> filter()` different from `SELECT ... WHERE`? What advantage does this give for time-series data?

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `iotlab_config.json not found` | `cp ~/Desktop/ESZG517_L1_Demo/iotlab_config.json .` |
| `Connection failed rc=5` | Wrong HiveMQ password in iotlab_config.json |
| `build_client() returned None` | Complete the TODO in build_client() |
| `[ERROR] Write failed` | Check InfluxDB token and bucket name |
| Node-RED "disconnected" after Deploy | Re-enter HiveMQ credentials → Update → Deploy |
| Grafana "No data" | Bucket name in Flux query must match iotlab_config.json exactly |
| Grafana parse error | Type query manually — copy-paste adds curly quotes |
| `git push` password rejected | Use Personal Access Token, not your GitHub password |
