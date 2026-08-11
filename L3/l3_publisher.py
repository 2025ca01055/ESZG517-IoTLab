"""
=============================================================================
ESZG517 — Internet of Things: Design and Development
Lab Session L3 — System Design and Multi-Sensor Integration
Project 2: Smart Home Automation

Student Name : Bhagyashri Maruti Pasalkar
USN          : 2025CA01055
Date         : 28/07/2026
=============================================================================

WHAT THIS FILE DOES:
--------------------
1. The IoTLab Emulator runs and writes smart home sensor data to:
   ~/.iotlab/emulator_data.json
2. This script reads that file every 5 seconds
3. It extracts sensor fields and publishes them to HiveMQ Cloud via MQTT

The IoTLab Emulator MUST be running with the Project 2 (Smart Home)
tab enabled BEFORE you run this script.

Architecture:
  [IoTLab Emulator] --> ~/.iotlab/emulator_data.json --> [This script] --> HiveMQ Cloud

HOW TO RUN:
-----------
1. Open IoTLab Emulator and enable Project 2 (Smart Home) tab
2. Fill in your HiveMQ credentials below
3. Run:  python3 l3_publisher.py
4. Open MQTT Explorer and watch your topics appear

SUBMISSION CHECKLIST:
---------------------
[ ] All TODOs completed
[ ] Script runs without errors
[ ] MQTT Explorer screenshot saved (shows full topic tree)
[ ] Terminal screenshot saved (shows publish cycles)
[ ] Code saved in your Project 2 folder
=============================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import json                                       # TODO-1  # json: converts Python dicts to JSON strings
import time                                       # TODO-2  # time: lets us pause the script with time.sleep()
import ssl                                           # ssl: handles encrypted (TLS) connections
from pathlib import Path                             # Path: handles file paths cleanly
import paho.mqtt.client as mqtt                     # TODO-3  # client: the MQTT client class


# =============================================================================
# FILE PATHS — do not change
# The emulator writes sensor data to these fixed locations
# =============================================================================

DATA_DIR  = Path.home() / ".iotlab"
DATA_FILE = DATA_DIR / "emulator_data.json"          # sensor readings from emulator
EMU_LOCK  = DATA_DIR / "emulator_ready.lock"         # emulator running signal
PUB_LOCK  = DATA_DIR / "publisher_active.lock"       # we create this to signal emulator


# =============================================================================
# CONFIGURATION — Fill in your details here
# =============================================================================

BROKER_URL  = "f0cb0c0ce8894c3aaf72971b5d3d6782.s1.eu.hivemq.cloud"     # Your HiveMQ cluster URL
BROKER_PORT =  8883                                # TODO-4  # 8883: secure MQTT port (TLS)
USERNAME    = "2025ca01055"                           # Your HiveMQ username
PASSWORD    = "Pasalkar@123"                        # Your HiveMQ password
YOUR_USN    = "2025CA01055"                             # e.g. "2023HT12345"

PUBLISH_INTERVAL = 5                                 # Seconds between each publish cycle


# =============================================================================
# MQTT TOPIC HIERARCHY
# Pattern: smarthome/<usn>/<room>/<sensor_type>/<data_type>
# =============================================================================

ROOM = "living_room"

# --- DEMO SENSORS (Instructor walks through these) ---
TOPIC_MOTION        = f"smarthome/{YOUR_USN}/{ROOM}/pir/motion"
TOPIC_LIGHT_STATE   = f"smarthome/{YOUR_USN}/{ROOM}/relay/light_state"
TOPIC_AMBIENT_LUX   = f"smarthome/{YOUR_USN}/{ROOM}/ambient/lux"

# --- ASSIGNMENT SENSORS (Students add these) ---
TOPIC_SMOKE         = f"smarthome/{YOUR_USN}/{ROOM}/mq2/smoke_ppm"
TOPIC_CO            = f"smarthome/{YOUR_USN}/{ROOM}/mq2/co_ppm"
TOPIC_DOOR          = f"smarthome/{YOUR_USN}/{ROOM}/reed/door_open"
TOPIC_WINDOW        = f"smarthome/{YOUR_USN}/{ROOM}/reed/window_open"
TOPIC_SOUND         = f"smarthome/{YOUR_USN}/{ROOM}/sound/db"
TOPIC_INDOOR_TEMP   = f"smarthome/{YOUR_USN}/{ROOM}/climate/indoor_temp"
TOPIC_INDOOR_HUM    = f"smarthome/{YOUR_USN}/{ROOM}/climate/indoor_humidity"


# =============================================================================
# EMULATOR HANDSHAKE
# =============================================================================

def check_emulator() -> bool:
    """
    Checks that the IoTLab Emulator is running and the Smart Home
    tab is enabled and producing data.
    Returns True if all checks pass, False otherwise.
    """
    if not EMU_LOCK.exists():
        print("[ERROR] IoTLab Emulator is not running.")
        print("        Open the emulator and enable the Project 2 (Smart Home) tab.")
        return False

    if not DATA_FILE.exists():
        print("[ERROR] Emulator data file not found.")
        print("        Enable the Smart Home tab in the emulator.")
        return False

    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        if not data.get("meta", {}).get("smarthome_enabled", False):
            print("[ERROR] Smart Home tab is not enabled in the emulator.")
            return False

        last_updated = data.get("meta", {}).get("last_updated", 0)
        age = time.time() - last_updated
        if age > 15:
            print(f"[ERROR] Emulator data is stale ({age:.0f}s old).")
            return False

    except Exception as e:
        print(f"[ERROR] Could not read emulator data: {e}")
        return False

    print("[OK] Emulator check passed. Smart Home data is live.")
    return True


def read_emulator_data() -> dict:
    """
    Reads the latest sensor values from the emulator data file.
    Returns the smarthome section as a dictionary.
    """
    with open(DATA_FILE, "r") as f:
        data = json.load(f)                       # TODO-5  # load(f): reads JSON from a file object
    return data.get("smarthome", {})


# =============================================================================
# MQTT CALLBACKS
# =============================================================================

def on_connect(client, userdata, flags, rc, properties=None):
    """
    Called automatically when the client connects to the broker.
    rc = 0 means success.
    """
    if rc == 0:                                # TODO-6  # 0: return code for successful connection
        print(f"[CONNECTED] Broker: {BROKER_URL}")
    else:
        print(f"[ERROR] Connection failed. Code: {rc}")


# =============================================================================
# PUBLISH FUNCTIONS — DEMO SENSORS
# =============================================================================

def publish_motion(client, motion):
    """
    Publishes a PIR motion event.
    retain=False — motion is a momentary event, not a state.
    QoS 1 — deliver at least once.
    """
    payload = json.dumps({"motion": motion, "room": ROOM})    # TODO-7  # json.dumps(): converts dict to JSON string
    client.publish(TOPIC_MOTION, payload, qos=1, retain=False)   # TODO-8  # publish(topic, payload, qos, retain)
    print(f"  [PIR]     motion={motion}")


def publish_light_state(client, light_state):
    """
    Publishes the relay/light state.
    retain=True — new subscribers must immediately know the current light state.
    QoS 1 — reliable delivery.
    """
    payload = json.dumps({"light_state": light_state, "room": ROOM}) # TODO-9  # light_state: the variable passed in
    client.publish(TOPIC_LIGHT_STATE, payload, qos=1, retain=True) # TODO-10  # True: retain the last light state
    print(f"  [RELAY]   light_state={light_state}")


def publish_ambient_lux(client, lux):
    """
    Publishes ambient light level in lux.
    retain=False — continuous reading, no need to retain.
    """
    payload = json.dumps({"ambient_lux": lux, "room": ROOM})
    client.publish(TOPIC_AMBIENT_LUX, payload, qos=0, retain=False)        # TODO-11  # TOPIC_AMBIENT_LUX: the topic constant defined above
    print(f"  [LIGHT]   ambient_lux={lux} lux")


# =============================================================================
# PUBLISH FUNCTIONS — ASSIGNMENT SENSORS
# Follow the exact same pattern as the demo functions above.
# Each function must:
#   1. Build a payload dict with the sensor value and room name
#   2. Convert to JSON with json.dumps()
#   3. Call client.publish() with the correct topic, qos=0, retain=False
#   4. Print a confirmation line
# =============================================================================

def publish_smoke(client, smoke_ppm):
    """
    Publishes smoke level in ppm.
    retain=False — continuous sensor reading.
    """
    payload = json.dumps({"smoke_ppm": smoke_ppm, "room": ROOM})
    client.publish(TOPIC_SMOKE, payload, qos=0, retain=False)
    print(f"  [SMOKE]   smoke_ppm={smoke_ppm} ppm")


def publish_co(client, co_ppm):
    """
    Publishes carbon monoxide level in ppm.
    retain=False — continuous sensor reading.
    """
    payload = json.dumps({"co_ppm": co_ppm, "room": ROOM})
    client.publish(TOPIC_CO, payload, qos=0, retain=False)
    print(f"  [CO]      co_ppm={co_ppm} ppm")


def publish_door(client, door_open):
    """
    Publishes door state.
    retain=True — new subscribers should know the current state.
    """
    payload = json.dumps({"door_open": door_open, "room": ROOM})
    client.publish(TOPIC_DOOR, payload, qos=1, retain=True)
    print(f"  [DOOR]    door_open={door_open}")


def publish_window(client, window_open):
    """
    Publishes window state.
    retain=True — new subscribers should know the current state.
    """
    payload = json.dumps({"window_open": window_open, "room": ROOM})
    client.publish(TOPIC_WINDOW, payload, qos=1, retain=True)
    print(f"  [WINDOW]  window_open={window_open}")


def publish_sound(client, sound_db):
    """
    Publishes sound level in dB.
    retain=False — continuous sensor reading.
    """
    payload = json.dumps({"sound_db": sound_db, "room": ROOM})
    client.publish(TOPIC_SOUND, payload, qos=0, retain=False)
    print(f"  [SOUND]   sound_db={sound_db} dB")


def publish_indoor_temp(client, indoor_temp):
    """
    Publishes indoor temperature in °C.
    retain=False — continuous sensor reading.
    """
    payload = json.dumps({"indoor_temp": indoor_temp, "room": ROOM})
    client.publish(TOPIC_INDOOR_TEMP, payload, qos=0, retain=False)
    print(f"  [TEMP]    indoor_temp={indoor_temp} °C")


def publish_indoor_humidity(client, indoor_humidity):
    """
    Publishes indoor humidity percentage.
    retain=False — continuous sensor reading.
    """
    payload = json.dumps({"indoor_humidity": indoor_humidity, "room": ROOM})
    client.publish(TOPIC_INDOOR_HUM, payload, qos=0, retain=False)
    print(f"  [HUMID]   indoor_humidity={indoor_humidity}%")


# =============================================================================
# MAIN
# =============================================================================

def main():

    # Step 1: Check emulator is running
    if not check_emulator():
        return

    # Step 2: Create publisher lock file
    PUB_LOCK.touch()

    # Step 3: Create MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "smarthome_publisher") # TODO-12  # VERSION2: callback API version

    # Step 4: Attach callbacks
    client.on_connect = on_connect                      # TODO-13  # on_connect: the function defined above

    # Step 5: Set credentials
    client.username_pw_set(USERNAME, PASSWORD)        # TODO-14  # USERNAME: the username constant defined above

    # Step 6: Enable TLS
    client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    # Step 7: Connect
    print(f"Connecting to {BROKER_URL}:{BROKER_PORT} ...")
    client.connect(BROKER_URL, BROKER_PORT, keepalive=60) # TODO-15  # BROKER_PORT: the port constant defined above

    # Step 8: Start background network loop
    client.loop_start()                                  # TODO-16  # loop_start(): starts background MQTT thread

    # Step 9: Wait for connection
    time.sleep(2)

    print(f"\nPublishing every {PUBLISH_INTERVAL} seconds. Press Ctrl+C to stop.\n")

    try:
        while True:
            print(f"\n--- Publish cycle ---")

            # Read latest values from emulator
            sensors = read_emulator_data()

            # Extract demo sensor values
            motion      = sensors.get("motion", False)
            light_state = sensors.get("light_state", "OFF")
            lux         = sensors.get("ambient_lux", 0.0)
            smoke_ppm = sensors.get("smoke_ppm", 0.0)
            co_ppm = sensors.get("co_ppm", 0.0)
            door_open = sensors.get("door_open", False)
            window_open = sensors.get("window_open", False)
            sound_db = sensors.get("sound_db", 0.0)
            indoor_temp = sensors.get("indoor_temp", 0.0)
            indoor_humidity = sensors.get("indoor_humidity", 0.0)

            # Publish demo sensors
            publish_motion(client, motion)
            publish_light_state(client, light_state)
            publish_ambient_lux(client, lux)
            publish_smoke(client, smoke_ppm)
            publish_co(client, co_ppm)
            publish_door(client, door_open)
            publish_window(client, window_open)
            publish_sound(client, sound_db)
            publish_indoor_temp(client, indoor_temp)
            publish_indoor_humidity(client, indoor_humidity)

            # ---- ASSIGNMENT: Extract values from emulator and publish ----
            # Follow this pattern for each sensor:
            #   value = sensors.get("field_name", default_value)
            #   publish_xxx(client, value)
            #
            # Field names available in emulator data:
            #   smoke_ppm, co_ppm, door_open, window_open,
            #   sound_db, indoor_temp, indoor_humidity

            # TODO-A8:  Extract smoke_ppm and publish
            # TODO-A9:  Extract co_ppm and publish
            # TODO-A10: Extract door_open and publish
            # TODO-A11: Extract window_open and publish
            # TODO-A12: Extract sound_db and publish
            # TODO-A13: Extract indoor_temp and publish
            # TODO-A14: Extract indoor_humidity and publish

            time.sleep(PUBLISH_INTERVAL)            # TODO-17  # sleep(seconds): pause before next cycle

    except KeyboardInterrupt:
        print("\n[STOPPED] Publisher shut down cleanly.")
        client.loop_stop()
        client.disconnect()
        if PUB_LOCK.exists():
            PUB_LOCK.unlink()


if __name__ == "__main__":                             # TODO-18  # __name__: equals "__main__" when run directly
    main()
