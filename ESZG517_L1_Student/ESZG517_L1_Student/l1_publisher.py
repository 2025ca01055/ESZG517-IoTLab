"""
============================================================
ESZG517 — Internet of Things: Design and Development
Lab Session L1 — Sensor to Cloud
Student Skeleton File: l1_publisher.py

Name   : Bhagyashri Maruti Pasalkar
USN    : 2025ca01055
Date   : 02/07/2026

How this file works:
  1. The IoTLab Emulator runs and writes sensor data to a
     shared file on your computer (~/.iotlab/emulator_data.json)
  2. This script reads that file every 5 seconds
  3. It extracts 5 sensor fields and publishes them to HiveMQ
     Cloud as a JSON payload via MQTT over TLS

  Emulator must be running BEFORE you run this script.
  Enable a sensor panel in the emulator first.

Architecture:
  [IoTLab Emulator] --> emulator_data.json --> [This script] --> HiveMQ Cloud
============================================================
"""

# ============================================================
# SECTION 1 — IMPORTS
# Already provided. Do not change anything here.
# ============================================================
import sys
import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
from pathlib import Path


# ============================================================
# SECTION 2 — FILE PATHS
# These paths are identical to the paths used by the emulator.
# Do not change these — they are fixed for the whole course.
# ============================================================

DATA_DIR  = Path.home() / ".iotlab"
DATA_FILE = DATA_DIR / "emulator_data.json"    # sensor readings from emulator
EMU_LOCK  = DATA_DIR / "emulator_ready.lock"   # emulator running signal
PUB_LOCK  = DATA_DIR / "publisher_active.lock" # you create this to signal emulator


# ============================================================
# SECTION 3 — YOUR CONFIGURATION
# Fill in your personal details below.
# ============================================================

# TODO 3.1 — Replace with your HiveMQ Cloud cluster URL
BROKER   = "f0cb0c0ce8894c3aaf72971b5d3d6782.s1.eu.hivemq.cloud"

# TODO 3.2 — Port for TLS. HiveMQ Cloud requires 8883.
PORT     = 8883  # TODO: set the correct port

# TODO 3.3 — Your HiveMQ credentials
USERNAME = "2025ca01055"
PASSWORD = "Pasalkar@123"

# TODO 3.4 — Your university student number (USN)
# This appears in the MQTT topic so the instructor can
# identify your data in HiveMQ and InfluxDB.
DEVICE_ID = "2025ca01055"

# TODO 3.5 — Construct your MQTT topic using your DEVICE_ID
# Format: eszg517/lab/weather/<your_USN>
TOPIC = "eszg517/lab/weather/" + DEVICE_ID
print ("eszg517/lab/weather/ {DEVICE_ID}")

# How often to publish (seconds) — do not change
PUBLISH_INTERVAL = 5


# ============================================================
# SECTION 4 — HANDSHAKE WITH EMULATOR
# Before publishing, verify the emulator is running and
# producing data. This is the handshake step.
# ============================================================

def check_emulator() -> bool:
    """
    Verifies the IoTLab Emulator is running and producing data.

    Checks three things in order:
      1. EMU_LOCK file exists  --> emulator is open
      2. DATA_FILE exists      --> emulator has written at least once
      3. Data is fresh (<10s)  --> a sensor panel is enabled

    Returns:
        True if all checks pass, False otherwise.

    This function prints a clear error message for each failure
    so the student knows exactly what to fix.
    """

    # TODO 4.1 — Check the emulator lock file exists.
    # If EMU_LOCK does not exist, the emulator is not running.
    # Print: "[ERROR] IoTLab Emulator is not running."
    #        "        Start IoTLabEmulator before running this script."
    # Return False.
    #
    # Hint: use EMU_LOCK.exists() to check if the file exists.
  

    if not EMU_LOCK.exists():
        print("[ERROR] IoTLab Emulator is not running.")
        print("        Start IoTLabEmulator before running this script.")
        return False


    # TODO 4.2 — Check the data file exists.
    # If DATA_FILE does not exist, the emulator has not written any data yet.
    # This means no sensor panel has been enabled yet.
    # Print: "[ERROR] No sensor data found."
    #        "        Enable a sensor panel in the emulator (toggle the Enable switch)."
    # Return False.
    if not DATA_FILE.exists():
        print ("[ERROR] No sensor data found.")
        print("         Start IoTLabEmulator before running this script.")
        return False

    # TODO 4.3 — Check the data is fresh (not older than 10 seconds).
    # Read the data file and get the timestamp from data["meta"]["last_updated"].
    # Calculate age = int(time.time()) - timestamp
    # If age > 10: print a warning (not an error — publisher can still run)
    #   "[WARNING] Emulator data is Xs old. Is a sensor panel enabled?"
    #
    # Hint to read the file:
    #   with open(DATA_FILE) as f:
    #       data = json.load(f)
    #   timestamp = data["meta"]["last_updated"]
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        age = int(time.time()) - data["meta"]["last_updated"]
        if age > 10:
            print(f"[WARNING] Emulator data is {age}s old. Is a sensor panel enabled?")
    except Exception as e:
        print(f"[WARNING] Could not verify data freshness: {e}")


    # If all checks pass, return True
    return True


# ============================================================
# SECTION 5 — READ SENSOR DATA FROM EMULATOR FILE
# ============================================================

def read_emulator_data() -> dict:
    """
    Reads the latest sensor data written by the IoTLab Emulator.

    The emulator writes ALL sensor fields to the data file.
    This function reads the file and returns the weather section.

    In-session fields (you use these today):
      temperature, humidity, pressure, co2_ppm, aqi

    Extended evaluation fields (add these for your submission):
      light_lux, wind_speed, wind_direction, rainfall_mm, battery_pct

    Returns:
        dict: the weather sensor readings, or empty dict on error.
    """

    # TODO 5.1 — Read and parse the data file.
    # Use a try/except block to handle file read errors gracefully.
    #
    # Inside try:
    #   Open DATA_FILE and load the JSON.
    #   The JSON structure is:
    #     {
    #       "weather": { "temperature": 26.4, "humidity": 62.1, ... },
    #       "smarthome": { ... },
    #       "meta": { "last_updated": 1713441600, ... }
    #     }
    #   Return data["weather"]
    #
    # Inside except (FileNotFoundError, json.JSONDecodeError, KeyError):
    #   Print: "[ERROR] Could not read emulator data: <error message>"
    #   Return {}   (empty dictionary)
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
        return data["weather"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"[ERROR] Could not read emulator data: {e}")
        return {}

    pass   # replace this with your implementation


# ============================================================
# SECTION 6 — BUILD YOUR MQTT PAYLOAD
# ============================================================

def build_payload(sensor_data: dict) -> dict:
    """
    Extracts the 5 in-session fields from the emulator data
    and constructs the MQTT payload dictionary.

    In-session fields:
      temperature  (°C)    from DHT22 sensor
      humidity     (%)     from DHT22 sensor
      pressure     (hPa)   from BMP280 sensor
      co2_ppm      (ppm)   from MQ135 sensor
      aqi          (index) from MQ135 sensor

    Parameters:
        sensor_data: the dictionary returned by read_emulator_data()

    Returns:
        dict: the complete payload ready for json.dumps()

    Note:
        sensor_data["temperature"] gives you the temperature value.
        Use the same key names as they appear in the emulator data.
        Add device_id and timestamp yourself.
    """

    # TODO 6.1 — Check if sensor_data is empty.
    # If the dictionary is empty (emulator not producing data),
    # print a warning and return {}.
    # Use: if not sensor_data:
    if not sensor_data:
        print(" [WARNING] No sensor data available. Is a sensor panel enabled?")
        return {}

    # TODO 6.2 — Extract the 5 in-session sensor fields.
    # Get each value from sensor_data using the correct key name.
    # Round each float to 2 decimal places using round(value, 2).
    # If a key is missing use .get("key", 0.0) as a safe default.
    #
    # temperature  = ...
    # humidity     = ...
    # pressure     = ...
    # co2_ppm      = ...
    # aqi          = ...

    temperature = round(sensor_data.get("temperature",       0.0), 2)
    humidity    = round(sensor_data.get("humidity",          0.0), 2) 
    pressure    = round(sensor_data.get("pressure",          0.0), 2) 
    co2_ppm     = round(sensor_data.get("co2_ppm",           0.0), 2)
    aqi         = round(sensor_data.get("aqi",               0.0), 2)
    light_lux   = round(sensor_data.get("light_lux",         0.0), 2)
    wind_speed  = round(sensor_data.get("wind_speed",        0.0), 2)
    wind_direction = round(sensor_data.get("wind_direction", 0.0), 2)
    rainfall_mm = round(sensor_data.get("rainfall_mm",       0.0), 2)
    battery_pct = round(sensor_data.get("battery_pct",       0.0), 2)

    # TODO 6.3 — Return the complete payload dictionary.
    # Include: device_id, temperature, humidity, pressure,
    #          co2_ppm, aqi, timestamp
    # timestamp = int(time.time())
     
    return {
        "device_id": DEVICE_ID,
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
        "co2": co2_ppm,
        "aqi": aqi,
        "light_level": light_lux,
        "wind_speed": wind_speed,
        "wind_direction": wind_direction,
        "rainfall": rainfall_mm,
        "battery_voltage": battery_pct,
        "rssi": sensor_data.get("rssi", -70),
        "timestamp": int(time.time())
}


    # ── EXTENDED EVALUATION ────────────────────────────────────
    # For your final submission, add these 5 fields to the payload:
    #
    #   light_lux      = round(sensor_data.get("light_lux",     0.0), 2)
    #   wind_speed     = round(sensor_data.get("wind_speed",    0.0), 2)
    #   wind_direction = round(sensor_data.get("wind_direction",0.0), 2)
    #   rainfall_mm    = round(sensor_data.get("rainfall_mm",   0.0), 2)
    #   battery_pct    = round(sensor_data.get("battery_pct",   0.0), 2)
    #
    # Include them in the returned dictionary alongside the 5 above.
    # ──────────────────────────────────────────────────────────


# ============================================================
# SECTION 7 — MQTT CALLBACKS
# ============================================================

def on_connect(client, userdata, flags, rc):
    """
    Called automatically when the MQTT client connects to the broker.

    rc = 0  : Connection successful
    rc = 4  : Bad username or password  <-- most common error
    rc = 3  : Server unavailable
    """

    # TODO 7.1 — Handle connection result.
    # If rc == 0: print success message with broker and topic.
    # If rc != 0: print error with the return code meaning.
    #
    # rc_messages = {
    #     0: "Connected successfully",
    #     1: "Incorrect protocol version",
    #     2: "Invalid client identifier",
    #     3: "Server unavailable",
    #     4: "Bad username or password",
    #     5: "Not authorised"
    # }
    rc_messages = {
        0:"Connected successfully", 1:"Incorrect protocol version",
        2:"Invalid client identifier", 3:"Server unavailable",
        4:"Bad username or password", 5:"Not authorised"
    }
    if rc == 0:
         print(f"[MQTT] Connected to {BROKER} | Topic: {TOPIC}")
    else:
         print(f"[MQTT] Connection failed — {rc_messages.get(rc, f'Unknown ({rc})')}")



def on_publish(client, userdata, mid):
    """Called when broker confirms message receipt (QoS 1 PUBACK)."""
	
    # TODO 7.2 — Print broker confirmation with message ID.
    print (f" (MOTT) Broker confirmed message (id-{mid})")

# ============================================================
# SECTION 8 — MQTT CLIENT SETUP
# ============================================================

def setup_mqtt_client():
    """
    Creates, configures, and connects the MQTT client.

    Steps:
      1. Create Client object with your DEVICE_ID
      2. Set username and password
      3. Enable TLS (required for HiveMQ Cloud port 8883)
      4. Register callbacks
      5. Connect to broker
      6. Start background network loop
    """

    # TODO 8.1 — Create MQTT client with your DEVICE_ID as client_id.
    client = mqtt.Client(client_id=DEVICE_ID)

    # TODO 8.2 — Set username and password.
    client.username_pw_set(USERNAME, PASSWORD)

    # TODO 8.3 — Enable TLS encryption.
    # client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    # TODO 8.4 — Register callbacks.
    client.on_connect = on_connect
    client.on_publish = on_publish 

    # TODO 8.5 — Connect to broker.
    # client.connect(BROKER, PORT, keepalive=60)
    client.connect(BROKER, PORT, keepalive=60)

    # TODO 8.6 — Start background loop.
    # client.loop_start()
    client.loop_start()

    time.sleep(2)   # wait for connection to establish
    return client


# ============================================================
# SECTION 9 — PUBLISHER LOCK FILE
# This signals to the emulator that your publisher is running.
# The emulator shows a green indicator when this file exists.
# ============================================================

def create_publisher_lock():
    """
    Creates publisher_active.lock so the emulator knows
    this publisher is connected.
    """
    # TODO 9.1 — Write your DEVICE_ID to the PUB_LOCK file.

    PUB_LOCK.write_text(DEVICE_ID)

    # The emulator checks this file's modification time to
    # confirm the publisher is still active.
  


def update_publisher_lock():
    """Touch the lock file to show publisher is still alive."""
    # TODO 9.2 — Update the file modification time.

    PUB_LOCK.touch()

    # Call this every publish cycle so the emulator knows
    # the publisher has not crashed.
    


def remove_publisher_lock():
    """Remove lock file on clean exit."""
    # TODO 9.3 — Delete the lock file on shutdown.
    # Use try/except in case the file does not exist.
    try:
         PUB_LOCK.unlink()
    except FileNotFoundError:
         pass


# ============================================================
# SECTION 10 — MAIN PUBLISH LOOP
# ============================================================

def main():
    print("=" * 60)
    print("  ESZG517 IoT Lab — L1 Publisher")
    print(f"  Device ID : {DEVICE_ID}")
    print(f"  Topic     : {TOPIC}")
    print(f"  Broker    : {BROKER}:{PORT}")
    print(f"  Data file : {DATA_FILE}")
    print("=" * 60)

    # TODO 10.1 — Run the emulator handshake check.
    # Call check_emulator().
    # If it returns False, print a message and exit.
    # Use sys.exit(1) to exit — import sys at the top if needed.
    if not check_emulator():
        sys.exit(1)

    print("\n[INFO] Emulator check passed. Connecting to HiveMQ...\n")

    # TODO 10.2 — Set up the MQTT client.
    client = setup_mqtt_client()


    # TODO 10.3 — Create the publisher lock file.
    create_publisher_lock()


    print(f"[INFO] Publishing to {TOPIC} every {PUBLISH_INTERVAL}s")
    print("[INFO] Press Ctrl+C to stop.\n")

    # TODO 10.4 — Implement the publish loop with clean shutdown.
    #
    try:
        while True:
             sensor_data = read_emulator_data()
             print("DEBUG:", sensor_data)
             payload_dict = build_payload(sensor_data)
    
             if payload_dict:   # only publish if we have valid data
                 payload_json = json.dumps(payload_dict)
                 client.publish(TOPIC, payload_json, qos=1)
                 ts = time.strftime("%H:%M:%S")
                 print(f"[{ts}] PUB --> {TOPIC}")
                 print(f"         {payload_json}\n")
    
             update_publisher_lock()   # keep the emulator indicator green
             time.sleep(PUBLISH_INTERVAL)
    
    except KeyboardInterrupt:
         print("\n[INFO] Stopping publisher...")
    
    finally:
         remove_publisher_lock()
         client.loop_stop()
         client.disconnect()
         print("[INFO] Disconnected cleanly.")


# ============================================================
# SECTION 11 — ENTRY POINT
# Do not change anything here.
# ============================================================

if __name__ == "__main__":
    main()
