# ESZG517 — Lab Sessions L4 + L5
## Combined Session Brief
### Smart Home: Node-RED + CoAP + Security + Anomaly Detection

---

## BEFORE YOU START

Unzip the folder. All commands must be run from inside this folder.

**Mac/Linux:**
```bash
cd path/to/ESZG517_L4L5_combined
```
**Windows:**
```cmd
cd path\to\ESZG517_L4L5_combined
```

---

## PART A — Complete Node-RED from L3 (15 minutes)

### Step 1: Start Node-RED

```bash
node-red
```

Open your browser: `http://localhost:1880`

### Step 2: Clear old configuration nodes

Before importing, clear any leftover configuration nodes from previous sessions.

Menu (☰) → **Configuration nodes**

You will see a list of config nodes. Click **unused** at the top right.
Delete every node listed — click each one and click Delete.

Click **Deploy** to save.

### Step 3: Import the flow

Menu (☰) → Import → select file → choose `l4_nodered_flow.json` → **Import**

### Step 4: Configure broker

Double-click **Subscribe: PIR Motion** → click **+** next to Server.

**Connection tab:**
- Server: your HiveMQ cluster URL (from your `iotlab_config.json`)
- Port: `8883`
- Check **Use TLS** → click **+** next to TLS dropdown → leave all fields blank → **Add**

**Security tab:**
- Username: `iotlab26S1`
- Password: your HiveMQ password

Click **Add** → **Done**.

Double-click **Subscribe: Light State** → set Server to same broker → **Done**.

Double-click **Publish: Light State** → set Server to same broker → click pencil icon → check TLS dropdown has a config selected (if empty, click + next to it, leave blank, click Add) → **Update** → **Done**.



### Step 5: Update topics

In all three mqtt nodes replace `YOUR_USN` with the USN you used in `l3_publisher_KEY.py`.

### Step 6: Start the emulator and publisher

Open IoTLab Emulator → enable **Project 2 (Smart Home)** tab.

In a new terminal run your L3 publisher:
```bash
python3 l3_publisher_KEY.py
```

### Step 7: Deploy

Click **Deploy** — all three mqtt nodes should show **connected**.

Open `http://localhost:1880/ui` — confirm Motion and Light panels show live values.

**Screenshot → save as `l4_nodered_dashboard.png`**

Export flow: Menu → Export → Download → save as `l4_nodered_flow_submitted.json`

---

## PART B — CoAP Server and Client (20 minutes)

### Step 1: Install aiocoap

**Mac/Linux:**
```bash
pip3 install aiocoap
```
**Windows:**
```cmd
pip install aiocoap
```

### Step 2: Open two terminals — both inside the ESZG517_L4L5_combined folder

**Terminal 1 — Start CoAP server:**

Mac/Linux:
```bash
python3 l4_coap_server.py
```
Windows:
```cmd
python l4_coap_server.py
```

Expected output:
```
[RESOURCE] coap://127.0.0.1/smarthome/bedroom1
[RESOURCE] coap://127.0.0.1/smarthome/bedroom2
[RESOURCE] coap://127.0.0.1/smarthome/living_room
[SERVER RUNNING] CoAP server is ready.
```

**Terminal 2 — Run CoAP client:**

Mac/Linux:
```bash
python3 l4_coap_client.py
```
Windows:
```cmd
python l4_coap_client.py
```

Note your latency values from Step 6 — you need them for Q3.

**Screenshot both terminals side by side → save as `l4_coap_screenshot.png`**

---

## PART C — Unencrypted MQTT + Wireshark (10 minutes)

### Step 1: Open Wireshark

- Mac: Applications → Wireshark
- Windows: Start Menu → Wireshark
- Linux: `wireshark` in terminal

Double-click **Loopback: lo0** (Mac/Linux) or **Adapter for loopback traffic capture** (Windows).

In the filter bar type `mqtt` and press Enter.

### Step 2: Kill any existing Mosquitto and start plain broker

**Mac/Linux:**
```bash
pkill mosquitto
mosquitto
```
**Windows:**
```cmd
taskkill /F /IM mosquitto.exe
mosquitto
```

### Step 3: Subscribe (new terminal, inside ESZG517_L4L5_combined folder)

**Mac/Linux:**
```bash
mosquitto_sub -h localhost -t "smarthome/demo/living_room/relay/light_state" -v
```
**Windows:**
```cmd
mosquitto_sub -h localhost -t "smarthome/demo/living_room/relay/light_state" -v
```

### Step 4: Publish (another terminal, inside ESZG517_L4L5_combined folder)

**Mac/Linux:**
```bash
mosquitto_pub -h localhost -t "smarthome/demo/living_room/relay/light_state" -m "{\"light_state\": \"ON\", \"room\": \"living_room\"}"
```
**Windows:**
```cmd
mosquitto_pub -h localhost -t "smarthome/demo/living_room/relay/light_state" -m "{\"light_state\": \"ON\", \"room\": \"living_room\"}"
```

Click the **Publish Message** packet in Wireshark. Read the payload in the bottom panel.

Answer Q11 based on what you see.

**Stop the plain Mosquitto broker with Ctrl+C.**

---

## PART D — TLS Encrypted MQTT + Wireshark (10 minutes)

Keep Wireshark running with the `mqtt` filter.

### Step 1: Start TLS Mosquitto broker (inside ESZG517_L4L5_combined folder)

**Mac/Linux:**
```bash
mosquitto -c mosquitto_tls.conf
```
**Windows:**
```cmd
mosquitto -c mosquitto_tls.conf
```

### Step 2: Subscribe with TLS (new terminal, inside ESZG517_L4L5_combined folder)

**Mac/Linux:**
```bash
mosquitto_sub -h localhost -p 8883 --cafile certs/ca.crt -t "smarthome/demo/living_room/relay/light_state" -v
```
**Windows:**
```cmd
mosquitto_sub -h localhost -p 8883 --cafile certs\ca.crt -t "smarthome/demo/living_room/relay/light_state" -v
```

### Step 3: Publish with TLS (another terminal, inside ESZG517_L4L5_combined folder)

**Mac/Linux:**
```bash
mosquitto_pub -h localhost -p 8883 --cafile certs/ca.crt -t "smarthome/demo/living_room/relay/light_state" -m "{\"light_state\": \"ON\", \"room\": \"living_room\"}"
```
**Windows:**
```cmd
mosquitto_pub -h localhost -p 8883 --cafile certs\ca.crt -t "smarthome/demo/living_room/relay/light_state" -m "{\"light_state\": \"ON\", \"room\": \"living_room\"}"
```

Observe Wireshark — the Publish Message packet is gone. Subscriber terminal still shows the message received.

Answer Q12 based on what you observe.

---

## PART E — Anomaly Detection in Google Colab (15 minutes)

### Step 1: Open Google Colab

Go to: **https://colab.research.google.com**

Click **Upload notebook** → upload `l5_anomaly_detection.ipynb`

### Step 2: Upload sensor data

Left panel → folder icon → upload icon → upload `l5_sensor_data.csv`

### Step 3: Run all 4 cells in order

Click ▶ on each cell. Wait for each to finish before running the next.

### Step 4: Download the graph

After Cell 4 runs, right-click `l5_anomaly_graph.png` in the Files panel → Download.

Save as `l5_anomaly_graph.png`.

Answer Q13 based on the graph.

---

## GitHub Submission

Push everything to your `ESZG517-Project2` repository:

```
ESZG517-Project2/
├── L3/
│   ├── l3_publisher.py
│   ├── l3_nodered_flow.json
│   ├── l3_mqttexplorer.png
│   └── l3_nodered_dashboard.png
├── L4/
│   ├── l4_coap_server.py
│   ├── l4_coap_client.py
│   ├── l4_nodered_flow_submitted.json
│   ├── l4_nodered_dashboard.png
│   ├── l4_coap_screenshot.png
│   └── l4l5_questions.txt
└── L5/
    ├── l5_anomaly_detection.ipynb
    ├── l5_sensor_data.csv
    └── l5_anomaly_graph.png
```

---

*ESZG517 — Internet of Things: Design and Development*
*Instructor: Aayush Basavesh | BITS Pilani WILP*
