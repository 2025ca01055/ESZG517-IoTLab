"""
╔══════════════════════════════════════════════════════════════════╗
║  ESZG517 — IoT Systems and Applications                         ║
║  Lab Session L2 — Storage, Query & Visualisation                ║
║  File : l2_subscriber.py          (Student Version)             ║
╚══════════════════════════════════════════════════════════════════╝

HOW THIS FILE WORKS
───────────────────
  Each function has a box showing the exact code to type.
  Read the box → type it into the blank below → run and verify.

SETUP BEFORE RUNNING
────────────────────
  1. Copy iotlab_config.json from your L1 folder into this folder
  2. pip install paho-mqtt influxdb-client
  3. Make sure l2_db_writer.py is in the same folder as this file
  4. Run the emulator + l1_publisher.py in a separate terminal first

PIPELINE
────────
  Emulator → l1_publisher.py → HiveMQ → l2_subscriber.py → l2_db_writer.py → InfluxDB → Grafana

SENSOR SPLIT
────────────
  DEMO (follow instructor):   temperature, humidity, pressure, co2, aqi
  YOUR ASSIGNMENT:            light_level, wind_speed, rainfall, battery_voltage, rssi
"""

import json
import ssl
import os
import paho.mqtt.client as mqtt
from l2_db_writer import write_to_influxdb

# ── Config loader (already done for you) ──────────────────────────────────────

def find_config() -> str:
    search_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "iotlab_config.json"),
        os.path.expanduser("~/Desktop/ESZG517_L1_Demo/iotlab_config.json"),
        os.path.expanduser("~/Desktop/IoTLab/iotlab_config.json"),
        "iotlab_config.json",
    ]
    for path in search_paths:
        if os.path.exists(path):
            print(f"[CONFIG] Loaded from: {path}")
            return path
    raise FileNotFoundError(
        "\n[ERROR] iotlab_config.json not found.\n"
        "Fix: Copy iotlab_config.json from your L1 folder into this folder."
    )

with open(find_config()) as f:
    config = json.load(f)

BROKER    = config["mqtt"]["broker"]
PORT      = config["mqtt"]["port"]
USERNAME  = config["mqtt"]["username"]
PASSWORD  = config["mqtt"]["password"]
DEVICE_ID = config["device"]["weather_id"]
TOPIC     = config["mqtt"]["topics"]["weather"] + "/+"


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 1 — on_connect
# ══════════════════════════════════════════════════════════════════════════════

def on_connect(client, userdata, flags, rc):
    # ╔══ ANSWER — type the lines below into the blank ══════════════════════╗
    #                                                                         #
    #   if rc == 0:                                                           #
    #       print("[INFO] Connected to HiveMQ Cloud.")                       #
    #       client.subscribe(TOPIC, qos=1)                                   #
    #       print(f"[INFO] Subscribed to {TOPIC} with QoS 1.")               #
    #   else:                                                                 #
    #       print(f"[ERROR] Connection failed, rc={rc}")                     #
    #                                                                         #
    # ╚═════════════════════════════════════════════════════════════════════╝

    # ── TYPE YOUR CODE HERE ───────────────────────────────────────────────────
        if rc == 0: 
              print("[INFO] Connected to HiveMQ Cloud.")
              client.subscribe(TOPIC, qos=1) 
              print(f"[INFO] Subscribed to {TOPIC} with QoS 1.")
        else: 
            print(f"[ERROR] Connection failed, rc={rc}")
            print("       check HiveMQ credentiels in iotlab_congig.json")

    # ── END ───────────────────────────────────────────────────────────────────
    

# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 2 — on_message
# ══════════════════════════════════════════════════════════════════════════════

def on_message(client, userdata, msg):
    # ╔══ ANSWER — type the lines below into the blank ══════════════════════╗
    #                                                                         #
    #   try:                                                                  #
    #       data = json.loads(msg.payload.decode("utf-8"))                   #
    #                                                                         #
    #       # pre-processing — already done, do not change                   #
    #       data["co2"] = data.pop("co2_ppm", data.get("co2", 0.0))         #
    #       import random                                                     #
    #       data.setdefault("light_level",     round(random.uniform(200,800),1))  #
    #       data.setdefault("wind_speed",      round(random.uniform(0,10),1))     #
    #       data.setdefault("rainfall",        round(random.uniform(0,2),2))      #
    #       data.setdefault("battery_voltage", round(random.uniform(3.6,4.2),2))  #
    #       data.setdefault("rssi",            random.randint(-80,-50))           #
    #                                                                         #
    #       print(                                                            #
    #           f"[DATA] {data.get('device_id','?')} | "                     #
    #           f"temp={data.get('temperature','?')}°C  "                    #
    #           f"hum={data.get('humidity','?')}%  "                         #
    #           f"co2={data.get('co2','?')}ppm  "                            #
    #           f"aqi={data.get('aqi','?')}  "                               #
    #           f"light={data.get('light_level','?')}lux  "                  #
    #           f"rssi={data.get('rssi','?')}dBm"                            #
    #       )                                                                 #
    #                                                                         #
    #       write_to_influxdb(data)                                          #
    #                                                                         #
    #   except json.JSONDecodeError as e:                                    #
    #       print(f"[WARNING] Could not parse JSON: {e}")                    #
    #   except Exception as e:                                               #
    #       print(f"[WARNING] Error in on_message: {e}")                     #
    #                                                                         #
    # ╚═════════════════════════════════════════════════════════════════════╝

    # ── TYPE YOUR CODE HERE ───────────────────────────────────────────────────

        try:                                                                  
           data = json.loads(msg.payload.decode("utf-8"))                   
                                                                             
           # pre-processing — already done, do not change                   
           data["co2"] = data.pop("co2_ppm", data.get("co2", 0.0))         
           import random                                                     
           data.setdefault("light_level",     round(random.uniform(200,800),1))  
           data.setdefault("wind_speed",      round(random.uniform(0,10),1))     
           data.setdefault("rainfall",        round(random.uniform(0,2),2))      
           data.setdefault("battery_voltage", round(random.uniform(3.6,4.2),2))  
           data.setdefault("rssi",            random.randint(-80,-50))           
                                                                             
           print(                                                            
               f"[DATA] {data.get('device_id','?')} | "                     
               f"temp={data.get('temperature','?')}°C  "                    
               f"hum={data.get('humidity','?')}%  "                         
               f"co2={data.get('co2','?')}ppm  "                            
               f"aqi={data.get('aqi','?')}  "                               
               f"light={data.get('light_level','?')}lux  "                  
               f"rssi={data.get('rssi','?')}dBm"                            
           )                                                                 
                                                                             
           write_to_influxdb(data)                                          
                                                                             
        except json.JSONDecodeError as e:                                    
           print(f"[WARNING] Could not parse JSON: {e}")                    
        except Exception as e:                                               
           print(f"[WARNING] Error in on_message: {e}") 

    # ── END ───────────────────────────────────────────────────────────────────
        pass


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 3 — build_client
# ══════════════════════════════════════════════════════════════════════════════

def build_client():
    # ╔══ ANSWER — type the lines below into the blank ══════════════════════╗
    #                                                                         #
    #   client = mqtt.Client(client_id=DEVICE_ID + "_sub",                  #
    #                        clean_session=True)                             #
    #   client.username_pw_set(USERNAME, PASSWORD)                           #
    #                                                                         #
    #   context = ssl.create_default_context()                               #
    #   context.check_hostname = False                                       #
    #   context.verify_mode = ssl.CERT_NONE                                  #
    #   client.tls_set_context(context)                                      #
    #                                                                         #
    #   client.on_connect = on_connect                                       #
    #   client.on_message = on_message                                       #
    #   return client                                                         #
    #                                                                         #
    # ╚═════════════════════════════════════════════════════════════════════╝

    # ── TYPE YOUR CODE HERE ───────────────────────────────────────────────────
        client = mqtt.Client(client_id= DEVICE_ID + "_sub",                  
                            clean_session=True)                             
        client.username_pw_set(USERNAME, PASSWORD)                           
                                                                             
        context = ssl.create_default_context()                               
        context.check_hostname = False                                       
        context.verify_mode = ssl.CERT_NONE                                  
        client.tls_set_context(context)                                      
                                                                             
        client.on_connect = on_connect                                       
        client.on_message = on_message                                       
        return client 


    # ── END ───────────────────────────────────────────────────────────────────
    

# ══════════════════════════════════════════════════════════════════════════════
# MAIN — already complete, do not change
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 62)
    print("  ESZG517 IoT Lab — L2 Subscriber (Python path)")
    print(f"  Device ID : {DEVICE_ID}")
    print(f"  Topic     : {TOPIC}")
    print(f"  Broker    : {BROKER}:{PORT}")
    print("=" * 62)

    client = build_client()
    if client is None:
        print("[ERROR] build_client() returned None — complete the TODO first.")
        raise SystemExit(1)

    print("[INFO] Connecting to HiveMQ Cloud...")
    client.connect(BROKER, PORT, keepalive=60)
    print("[INFO] Listening for messages. Press Ctrl+C to stop.\n")

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Disconnecting...")
        client.disconnect()
        print("[INFO] Stopped.")
