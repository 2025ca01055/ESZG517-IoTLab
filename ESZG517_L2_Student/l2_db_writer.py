"""
╔══════════════════════════════════════════════════════════════════╗
║  ESZG517 — IoT Systems and Applications                         ║
║  Lab Session L2 — Storage, Query & Visualisation                ║
║  File : l2_db_writer.py           (Student Version)             ║
╚══════════════════════════════════════════════════════════════════╝

HOW THIS FILE WORKS
───────────────────
  Each function has a box showing the exact code to type.
  Read the box → type it into the blank below → run the self-test.

  Run this file directly first to verify InfluxDB before connecting
  the subscriber:
      python3 l2_db_writer.py

KEY CONCEPTS
────────────
  Measurement : table name  →  "weather_station"
  Tag         : indexed metadata, used for filtering  →  device_id
  Field       : actual sensor value  →  temperature, humidity, etc.
  Point       : one row  =  timestamp + tags + fields
  Bucket      : data container (from iotlab_config.json)
  Flux        : InfluxDB query language — pipeline model

NOTE: The InfluxDB Cloud web UI shows SQL mode only (UI change).
      The API still supports Flux — your Python queries and Grafana
      dashboards both work correctly via the API.
"""

import os
import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

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

INFLUX_URL    = config["influxdb"]["url"]
INFLUX_TOKEN  = config["influxdb"]["token"]
INFLUX_ORG    = config["influxdb"]["org"]
INFLUX_BUCKET = config["influxdb"]["bucket"]
MEASUREMENT   = "weather_station"

# InfluxDB client — initialised once, reused for every write
_client    = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
_write_api = _client.write_api(write_options=SYNCHRONOUS)
_query_api = _client.query_api()


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 1 — write_to_influxdb   (DEMO: sensors 1–5)
# ══════════════════════════════════════════════════════════════════════════════

def write_to_influxdb(data: dict) -> None:
    # ╔══ ANSWER — DEMO sensors 1–5 (type into blank, then add 6–10 below) ═╗
    #                                                                         #
    #   try:                                                                  #
    #       point = (                                                         #
    #           Point(MEASUREMENT)                                           #
    #           .tag("device_id",    str(data["device_id"]))                 #
    #           .field("temperature", float(data["temperature"]))            #
    #           .field("humidity",    float(data["humidity"]))               #
    #           .field("pressure",    float(data["pressure"]))               #
    #           .field("co2",         float(data["co2"]))                    #
    #           .field("aqi",         float(data["aqi"]))                    #
    #       )                                                                 #
    #       _write_api.write(bucket=INFLUX_BUCKET, record=point)             #
    #       print(f"[INFLUX] Written: {data['device_id']}  "                 #
    #             f"temp={data['temperature']}  co2={data['co2']}")          #
    #   except Exception as e:                                               #
    #       print(f"[ERROR] Write failed: {e}")                              #
    #                                                                         #
    # ╠══ ANSWER — YOUR ASSIGNMENT: add sensors 6–10 inside the Point ══════╣
    #                                                                         #
    #   After .field("aqi", ...) add these five lines:                       #
    #                                                                         #
    #           .field("light_level",     float(data["light_level"]))        #
    #           .field("wind_speed",      float(data["wind_speed"]))         #
    #           .field("rainfall",        float(data["rainfall"]))           #
    #           .field("battery_voltage", float(data["battery_voltage"]))    #
    #           .field("rssi",            int(data["rssi"]))                 #
    #                                                                         #
    # ╚═════════════════════════════════════════════════════════════════════╝

    # ── TYPE YOUR CODE HERE ───────────────────────────────────────────────────

    try:                                                                  
        point = (                                                         
               Point(MEASUREMENT)                                           
               .tag("device_id",    str(data["device_id"]))                 
               .field("temperature", float(data["temperature"]))            
               .field("humidity",    float(data["humidity"]))               
               .field("pressure",    float(data["pressure"]))               
               .field("co2",         float(data["co2"]))                    
               .field("aqi",         int(data["aqi"]))
               .field("light_level", float(data["light_level"]))
                .field("wind_speed", float(data["wind_speed"]))
                .field("rainfall", float(data["rainfall"]))
                .field("battery_voltage", float(data["battery_voltage"]))
                .field("rssi", int(data["rssi"]))     
                              
           )                                                                 
        _write_api.write(bucket=INFLUX_BUCKET, record=point)             
        print(
        f"[INFLUX] Written: {data['device_id']} "
        f"temp={data['temperature']} "
        f"hum={data['humidity']} "
        f"co2={data['co2']} "
        f"aqi={data['aqi']} "
        f"light={data['light_level']} "
        f"wind={data['wind_speed']} "
        f"rain={data['rainfall']} "
        f"battery={data['battery_voltage']} "
        f"rssi={data['rssi']}"
    )          
    except Exception as e:                                               
           print(f"[ERROR] Write failed: {e}")    

    # ── END ───────────────────────────────────────────────────────────────────
    pass


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 2 — query_recent
# ══════════════════════════════════════════════════════════════════════════════

def query_recent(field: str, window_minutes: int = 10) -> list:
    # ╔══ ANSWER — type the lines below into the blank ══════════════════════╗
    #                                                                         #
    #   try:                                                                  #
    #       flux = f'''                                                       #
    #       from(bucket: "{INFLUX_BUCKET}")                                  #
    #         |> range(start: -{window_minutes}m)                            #
    #         |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")        #
    #         |> filter(fn: (r) => r._field == "{field}")                    #
    #       '''                                                               #
    #       tables = _query_api.query(flux, org=INFLUX_ORG)                  #
    #       results = []                                                      #
    #       for table in tables:                                              #
    #           for record in table.records:                                  #
    #               results.append({                                          #
    #                   "time":  str(record.get_time()),                     #
    #                   "value": record.get_value()                          #
    #               })                                                        #
    #       return results                                                    #
    #   except Exception as e:                                               #
    #       print(f"[ERROR] Query failed: {e}")                              #
    #       return []                                                         #
    #                                                                         #
    # ╚═════════════════════════════════════════════════════════════════════╝

    # ── TYPE YOUR CODE HERE ───────────────────────────────────────────────────

    try:                                                                  
        flux = f'''                                                       
        from(bucket: "{INFLUX_BUCKET}")                                  
            |> range(start: -{window_minutes}m)                            
            |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")        
            |> filter(fn: (r) => r._field == "{field}")                    
        '''                                                               
        tables = _query_api.query(flux, org=INFLUX_ORG)                  
        results = []                                                      
        for table in tables:                                              
            for record in table.records:                                  
                results.append({                                          
                    "time":  str(record.get_time()),                     
                    "value": record.get_value()                          
                })                                                        
        return results                                                    
    except Exception as e:                                               
        print(f"[ERROR] Query failed: {e}")                              
        return []   
    # ── END ───────────────────────────────────────────────────────────────────
    


# ══════════════════════════════════════════════════════════════════════════════
# SELF-TEST — run this file directly first to verify InfluxDB works
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Running InfluxDB self-test...\n")

    test_data = {
        "device_id": "TEST_DEVICE", "temperature": 25.0, "humidity": 60.0,
        "pressure": 1013.0, "co2": 410.0, "aqi": 30.0,
        "light_level": 500.0, "wind_speed": 2.5, "rainfall": 0.0,
        "battery_voltage": 3.8, "rssi": -70
    }

    write_to_influxdb(test_data)

    print("\nQuerying temperature (last 5 min)...")
    results = query_recent("temperature", window_minutes=5)
    if results:
        print(f"  ✅ Found {len(results)} record(s). Latest: {results[-1]}")
    else:
        print("  ❌ No results — complete write_to_influxdb() and query_recent() first.")
