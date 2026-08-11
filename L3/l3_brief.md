# ESZG517 — Lab Session L3
## System Design and Multi-Sensor Integration
### Project 2: Smart Home Automation

**Duration:** 1.5 hours  
**Course Outcomes:** CO2, CO3

---

## Aim

To apply the ten-step IoT design methodology to a smart home scenario, produce a layered architecture diagram, implement a Python multi-sensor publisher, and build a Node-RED flow with auto-off logic and a live dashboard.

---

## Pre-Session Requirements

Complete these **before** the session starts.

- [ ] HiveMQ Cloud account active (same credentials as L1/L2)
- [ ] Python installed with `paho-mqtt`: `pip install paho-mqtt`
- [ ] Node-RED installed: `npm install -g --unsafe-perm node-red`
- [ ] Node-RED dashboard palette installed:
  - Open Node-RED → Menu (☰) → Manage Palette → Install → search `node-red-dashboard` → Install
- [ ] MQTT Explorer installed (free download: mqttexplorer.com)
- [ ] draw.io accessible at app.diagrams.net (no account needed)
- [ ] New GitHub repository created named `ESZG517-Project2`

---

## GitHub Setup (First 5 minutes of session)

Run these commands in your terminal. Do this **before** writing any code.

```bash
# Create your project folder
mkdir ESZG517-Project2
cd ESZG517-Project2

# Initialise git
git init
git branch -M main

# Connect to your GitHub repo (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ESZG517-Project2.git

# Create a README
echo "# ESZG517 Project 2 - Smart Home Automation" > README.md
git add README.md
git commit -m "Initial commit"
git push -u origin main
```

Place all L3 files inside this folder going forward.

---

## Part A — Architecture Diagram (15 minutes)

Open **app.diagrams.net** and create a layered architecture diagram for the smart home system.

Your diagram must show **four layers**:

| Layer | What goes here |
|---|---|
| Perception | PIR sensor, relay/light, ambient light sensor, gas sensor, reed switch, sound sensor, climate sensor |
| Network | MQTT/TLS arrows from sensors to broker |
| Middleware | HiveMQ Cloud broker |
| Application | Node-RED (auto-off logic + dashboard), MQTT Explorer |

**Label every arrow with its protocol** (MQTT/TLS, HTTP).  
**Export as PNG** and save as `l3_architecture.png` in your project folder.

---

## Part B — Python Multi-Sensor Publisher (50 minutes)

### Step 1: Configure credentials

Open `l3_publisher.py`. Fill in your HiveMQ credentials at the top:

```python
BROKER_URL = "YOUR_CLUSTER.s2.eu.hivemq.cloud"
PASSWORD   = "YOUR_PASSWORD"
YOUR_USN   = "YOUR_USN"
```

### Step 2: Complete the demo TODOs (instructor walks through)

The instructor will demonstrate completing TODOs 1–19 for the three demo sensors:
- PIR motion
- Light relay state (with `retain=True`)
- Ambient light (lux)

Follow along and fill in your blanks at the same time.

### Step 3: Complete the assignment TODOs

Complete TODOs A1–A21 to add the remaining four sensor types:
- MQ2 gas (smoke_ppm, co_ppm)
- Reed switch (door_open, window_open)
- Sound (sound_db)
- Indoor climate (indoor_temp, indoor_humidity)

Follow the exact same pattern as the demo sensors.

### Step 4: Run and verify

```bash
python l3_publisher.py
```

Open **MQTT Explorer**, connect to your HiveMQ cluster, and verify:
- All topics appear under `smarthome/YOUR_USN/living_room/`
- Light state topic shows the retained value immediately on connect

**Take a screenshot of MQTT Explorer showing your full topic tree.**  
Save it as `l3_mqttexplorer.png`.

---

## Part C — Node-RED Auto-Off + Dashboard (25 minutes)

### Step 1: Start Node-RED

```bash
node-red
```

Open your browser and go to: `http://localhost:1880`

### Step 2: Import the student flow

Menu (☰) → Import → Paste the contents of `l3_nodered_flow.json` → Import

### Step 3: Configure the broker node

Double-click the **Subscribe: PIR Motion** node.
Click the **+** button next to the Server dropdown to create a new broker config.

In the **Connection** tab:
- Name: HiveMQ Cloud
- Server: your HiveMQ cluster URL
- Port: 8883
- Check **Use TLS** then click the **+** next to the TLS dropdown, leave all fields blank, click **Add**

In the **Security** tab:
- Username: iotlab26S1
- Password: your HiveMQ password

Click **Add** then **Done**.

Now double-click **Subscribe: Light State**, set Server to **HiveMQ Cloud**, click **Done**.

Click **Deploy** - both Subscribe nodes should show **connected**.

> ⚠️ **Important:** Do NOT keep clicking Deploy repeatedly. If you deploy more than 4-5 times in a short period, HiveMQ will temporarily block your connection for a few minutes (rate limiting). Configure your broker once, deploy once. If you get stuck on connecting, wait 2 minutes and restart Node-RED.

### Step 4: Update topics

In every `mqtt in` and `mqtt out` node, replace `YOUR_USN` with your actual USN.

### Step 5: Complete the TODO function nodes

**Auto-Off Timer Logic node:**  
Double-click it. Read the instructions inside the node carefully. Implement the logic.

**Format Light State node:**  
Double-click it. Read the instructions. Implement the one-line format.

### Step 6: Deploy

Click the red **Deploy** button (top right).  
All nodes should show a green dot underneath them.

### Step 7: Open the dashboard

Go to: `http://localhost:1880/ui`

You should see the Smart Home dashboard with:
- Motion status panel
- Light state panel

**Take a screenshot of your dashboard.**  
Save it as `l3_nodered_dashboard.png`.

### Step 8: Export your flow

Menu (☰) → Export → Download → Save as `l3_nodered_flow_submitted.json`.

---

## Git Commit (Last 5 minutes)

```bash
cd ESZG517-Project2
git add l3_publisher.py l3_architecture.png l3_mqttexplorer.png l3_nodered_dashboard.png l3_nodered_flow_submitted.json
git commit -m "L3: Smart home publisher and Node-RED flow"
git push
```

---

## Post-Session Submission (Due before next lab)

| # | Item | Format |
|---|---|---|
| 1 | Ten-step design document (steps 1–6) | `l3_design.txt` or `l3_design.pdf` |
| 2 | Architecture diagram | `l3_architecture.png` |
| 3 | Complete publisher | `l3_publisher.py` |
| 4 | Node-RED flow | `l3_nodered_flow_submitted.json` |
| 5 | MQTT Explorer screenshot | `l3_mqttexplorer.png` |
| 6 | Node-RED dashboard screenshot | `l3_nodered_dashboard.png` |
| 7 | GitHub repository link | Submit on eLearn |

All files must be committed to your `ESZG517-Project2` GitHub repository.

---

## Ten-Step Design Document — What to Write

Complete steps 1–6 for this scenario:

> A living room has one PIR motion sensor and one relay-controlled light. When motion is detected, the light turns ON. If no motion is detected for 60 seconds, the light turns OFF automatically. The system publishes sensor data to HiveMQ Cloud and processes it in Node-RED.

| Step | What to write |
|---|---|
| 1. Purpose & Requirements | What problem does it solve? What must it do? |
| 2. Process Specification | What data flows where, at what frequency? |
| 3. Domain Model | List all entities (devices, sensors, users) and how they relate |
| 4. Information Model | For each sensor, list fields, data types, units, valid ranges |
| 5. Service Specifications | What services does the system provide? (motion detection, auto-off, etc.) |
| 6. IoT Level | Which of the 6 IoT levels is this system? Justify in 2–3 sentences |

---

## Viva Questions (Be prepared to answer these)

1. Why does the light relay topic use `retain=True` but the motion topic does not?
2. In your topic hierarchy, how would a subscriber receive all sensor data from all rooms without subscribing to each topic individually?
3. What is the difference between QoS 0 and QoS 1? Which did you use for motion events and why?
4. If Node-RED restarts, will it immediately know the current light state? Why?
5. What would happen if two motion publishers for the same room ran simultaneously?

---

*ESZG517 — Internet of Things: Design and Development*  
*Instructor: Aayush Basavesh | BITS Pilani WILP*
