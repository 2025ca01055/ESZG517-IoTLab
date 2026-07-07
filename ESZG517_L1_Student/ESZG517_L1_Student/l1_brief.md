# LAB SESSION L1 — Sensor to Cloud
## ESZG517 Internet of Things: Design and Development
## Project 1 — Weather Station Pipeline
**Duration:** 2 hours | **Individual Submission**

---

## Context

In this session you are building the first link in a complete IoT pipeline — the publisher. Your code will read sensor data (from a physical ESP32 or the IoTLab Emulator) and transmit it securely to a cloud MQTT broker using the MQTT protocol.

This directly implements **IoT Level 2 architecture** from Contact Session 3 — a sensor node transmitting data through a network to a cloud middleware layer.

By the end of this session your sensor data must be visible on the HiveMQ Cloud broker and your code must be committed to your individual GitHub repository.

---

## Learning Objectives

By completing this session you will be able to:
- Configure a secure MQTT connection with TLS authentication
- Construct a structured JSON payload from sensor readings
- Select and justify an appropriate QoS level for IoT sensor data
- Publish sensor data to a cloud MQTT broker using the correct topic hierarchy
- Commit and push code to a personal GitHub repository

---

## Pre-Lab Requirements

Complete all of the following before the session begins:
- [ ] Python 3.10+ installed (`python3 --version`)
- [ ] paho-mqtt installed (`pip install paho-mqtt`)
- [ ] HiveMQ Cloud account created — credentials noted
- [ ] GitHub account created
- [ ] IoTLab Emulator running (if not using physical ESP32)
- [ ] IoTLab Emulator connected to HiveMQ Cloud (green dot in MQTT Config tab)

---

## Your Student Details

Fill this in before writing any code. Your USN will be used as your device identifier throughout the course.

```
Your USN        : _______________
HiveMQ Broker   : _______________
HiveMQ Username : _______________
Your MQTT Topic : eszg517/lab/weather/_______________
```

---

## Tools for This Session

| Tool | Purpose | Where |
|---|---|---|
| IoTLab Emulator | Hardware simulation | Provided executable |
| Python 3 + paho-mqtt | MQTT publisher code | Your laptop |
| HiveMQ Cloud Console | Verify messages arriving | hivemq.com |
| VS Code | Code editor | code.visualstudio.com |
| MQTT Explorer | Inspect live MQTT traffic | mqtt-explorer.com |

---

## Session Structure

| Time | Activity |
|---|---|
| 0:00 – 0:15 | Instructor introduction + pre-lab check |
| 0:15 – 0:30 | Read the skeleton code and understand the structure |
| 0:30 – 1:15 | Write your code — Tasks 1 to 5 |
| 1:15 – 1:35 | Test, debug, verify on HiveMQ console |
| 1:35 – 1:50 | Git setup and first commit |
| 1:50 – 2:00 | Instructor in-session check and Q&A |

---

## The IoT Pipeline You Are Building Today

```
[Sensor / Emulator]
        |
        | reads sensor values
        v
[Your Publisher Code]   <-- THIS IS WHAT YOU WRITE TODAY
        |
        | MQTT over TLS (port 8883)
        v
[HiveMQ Cloud Broker]
        |
        | (future sessions)
        v
[InfluxDB --> Grafana Dashboard]
```

---

## In-Session Tasks

### Task 1 — Understand the payload format

Before writing any code, read the payload specification carefully.
Every field has a name, data type, and unit.
Your code must produce JSON that exactly matches this specification.

**In-session payload — complete these 5 fields today:**

| Field | Type | Unit | Example value |
|---|---|---|---|
| `device_id` | string | — | `"21CS001"` |
| `temperature` | float | °C | `26.4` |
| `humidity` | float | % | `62.1` |
| `pressure` | float | hPa | `1013.2` |
| `co2_ppm` | float | ppm | `412.0` |
| `aqi` | float | AQI index | `52.0` |
| `timestamp` | int | Unix epoch seconds | `1713441600` |

**Extended evaluation payload — add these 5 fields for your final submission:**

| Field | Type | Unit |
|---|---|---|
| `light_lux` | float | lux |
| `wind_speed` | float | km/h |
| `wind_direction` | float | degrees 0–360 |
| `rainfall_mm` | float | mm/hr |
| `battery_pct` | float | % |

### Task 2 — Complete l1_publisher.py
Open the skeleton file. Complete every section marked TODO.
Read every comment carefully — the comments explain what to write and why.

### Task 3 — Run and verify
Run your publisher and verify messages are arriving in the HiveMQ Cloud console under your topic.

### Task 4 — Open MQTT Explorer
Connect MQTT Explorer to your HiveMQ cluster.
Find your topic in the tree.
Take a screenshot showing your topic and one complete JSON payload.
This screenshot is a submission requirement.

### Task 5 — Write your QoS justification
In a separate file called `l1_qos_justification.txt` write 200 to 300 words answering:

*Why did you choose QoS 1 for this sensor data pipeline? What would change if you used QoS 0? Under what conditions would QoS 2 be the correct choice? Use specific examples from the IoT domain to support your answer.*

---

## Git Setup — End of Session

Every student must maintain an individual private GitHub repository for the entire course. This repository is your primary submission artefact.

### First-time setup — do this once:

```bash
# 1. Create a new private repository on github.com named ESZG517-YourUSN
# 2. In your project folder run:

git init
git add l1_publisher.py l1_qos_justification.txt
git commit -m "L1: MQTT publisher — in-session submission"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ESZG517-YourUSN.git
git push -u origin main
```

Verify your files appear on github.com before leaving the session.

### For every subsequent session:

```bash
git add .
git commit -m "L2: Descriptive message about what you did"
git push
```

Use meaningful commit messages — they form part of your evaluation.

---

## In-Session Check — 10% of L1 marks

The instructor will verify the following during the last 10 minutes:
- [ ] Publisher running without errors
- [ ] Messages visible on HiveMQ Cloud console under your USN topic
- [ ] MQTT Explorer screenshot taken and shown
- [ ] GitHub repository created and L1 code pushed

---

## Final Submission Requirements — 90% of L1 marks

Submit via eLearn before the deadline:

| # | Item | Marks |
|---|---|---|
| 1 | `l1_publisher.py` — in-session version, all 5 fields working | 20 |
| 2 | `l1_publisher.py` — extended version, all 10 fields working | 20 |
| 3 | MQTT Explorer screenshot showing your topic and full payload | 10 |
| 4 | HiveMQ Cloud console screenshot showing messages arriving | 10 |
| 5 | `l1_qos_justification.txt` — 200 to 300 words, technically accurate | 25 |
| 6 | GitHub repository link — code committed with meaningful commit messages | 15 |
| **Total** | | **100** |

---

## Common Mistakes to Avoid

- Using port 1883 instead of 8883 — HiveMQ Cloud only accepts TLS on 8883
- Forgetting `client.loop_start()` before publishing — messages will silently not send
- Topic does not include your USN — your data cannot be identified or marked
- JSON field names do not match the specification — the subscriber will fail to parse your data
- Vague commit messages such as "fix" or "update" — marks are deducted

---

## Reference

- MQTT protocol and QoS levels: T1 Chapter 2, Contact Session 6 notes
- Python json module: `import json; json.dumps()`
- paho-mqtt documentation: https://pypi.org/project/paho-mqtt/
- HiveMQ Cloud documentation: https://docs.hivemq.com/hivemq-cloud/

---

*ESZG517 — Internet of Things: Design and Development*
*BITS Pilani — Work Integrated Learning Programmes*
*Instructor: Aayush Basavesh | April 2026*
