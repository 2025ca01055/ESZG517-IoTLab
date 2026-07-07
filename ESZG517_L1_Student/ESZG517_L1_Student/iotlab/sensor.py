"""
IoTLab Sensor Abstraction Layer
Medium-level API: sensor.send(field=value, ...)

Supports both:
  • Emulator users  — emulator publishes MQTT, framework subscribes
  • ESP32 users     — ESP32 publishes MQTT, same framework subscribes

Direct publish mode (publisher.py / test scripts):
  weather = WeatherStation(client)
  weather.send(temperature=26.4, humidity=62.1, pressure=1013.2)
"""

from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

log = logging.getLogger("iotlab.sensor")


# ══════════════════════════════════════════════════════════════════════════════
# SENSOR READING DATACLASS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SensorReading:
    """
    Universal container for any sensor reading.
    measurement : InfluxDB measurement name (e.g. 'weather', 'smarthome')
    device_id   : Unique node identifier
    tags        : InfluxDB tag key-value pairs (indexed, low-cardinality)
    fields      : InfluxDB field key-value pairs (sensor values)
    timestamp   : Unix epoch seconds (auto-set if not provided)
    """
    measurement: str
    device_id:   str
    tags:        dict[str, str]   = field(default_factory=dict)
    fields:      dict[str, Any]   = field(default_factory=dict)
    timestamp:   int              = field(default_factory=lambda: int(time.time()))

    def to_json(self) -> str:
        return json.dumps({
            "device_id":   self.device_id,
            "measurement": self.measurement,
            "tags":        self.tags,
            "fields":      self.fields,
            "timestamp":   self.timestamp,
        })

    def to_line_protocol(self) -> str:
        """
        Convert to InfluxDB line protocol string.
        Format: measurement,tag1=v1 field1=v1,field2=v2 timestamp_ns
        """
        tag_str = ",".join(
            f"{k}={v}" for k, v in sorted(self.tags.items()))
        measurement_tags = (
            f"{self.measurement},{tag_str}" if tag_str else self.measurement)

        def _fmt(v):
            if isinstance(v, bool):  return str(v).lower()
            if isinstance(v, int):   return f"{v}i"
            if isinstance(v, float): return f"{v}"
            return f'"{v}"'

        field_str = ",".join(
            f"{k}={_fmt(v)}" for k, v in self.fields.items())
        ts_ns = self.timestamp * 1_000_000_000
        return f"{measurement_tags} {field_str} {ts_ns}"

    @staticmethod
    def from_json(raw: str) -> "SensorReading":
        d = json.loads(raw)

        # Structured format (from framework publisher)
        if "fields" in d:
            return SensorReading(
                measurement=d.get("measurement", "unknown"),
                device_id=d.get("device_id", "unknown"),
                tags=d.get("tags", {}),
                fields=d.get("fields", {}),
                timestamp=d.get("timestamp", int(time.time())),
            )  

        # Flat format (from emulator or physical ESP32)
        device_id = d.get("device_id", "unknown")
        timestamp = d.get("timestamp", int(time.time()))

        # Infer measurement from device_id
        if any(x in device_id.lower() for x in ["smarthome", "home", "room"]):
            measurement = "smarthome"
        else:
            measurement = "weather"

        # Strings → tags, numbers/bools → fields
        skip = {"device_id", "timestamp"}
        tags   = {"device_id": device_id}
        fields = {}

        for k, v in d.items():
            if k in skip:
                continue
            if isinstance(v, bool):
                fields[k] = v
            elif isinstance(v, (int, float)):
                fields[k] = float(v)
            elif isinstance(v, str):
                tags[k] = v

        return SensorReading(
            measurement=measurement,
            device_id=device_id,
            tags=tags,
            fields=fields,
            timestamp=timestamp,
        )

# ══════════════════════════════════════════════════════════════════════════════
# BASE SENSOR CLASS
# ══════════════════════════════════════════════════════════════════════════════

class BaseSensor:
    """
    Base class for sensor abstractions.
    Subclasses define MEASUREMENT, REQUIRED_FIELDS, OPTIONAL_FIELDS,
    ALERT_THRESHOLDS, and FIELD_UNITS.
    """

    MEASUREMENT:     str
    REQUIRED_FIELDS: list[str]
    OPTIONAL_FIELDS: list[str]    = []
    ALERT_THRESHOLDS: dict        = {}
    FIELD_UNITS:      dict        = {}

    def __init__(self, client, device_id: str = "", location: str = "") -> None:
        """
        client    : IoTLabClient instance
        device_id : overrides config if provided
        location  : tag added to every reading
        """
        self._client    = client
        self._device_id = device_id or getattr(
            client.config.device, f"{self.MEASUREMENT}_id",
            f"ESZG517_{self.MEASUREMENT.title()}_01")
        self._location  = location or client.config.device.location
        self._count     = 0
        self._last_reading: Optional[SensorReading] = None

    def send(self, **fields) -> SensorReading:
        """
        Validate, package, publish, and write a sensor reading.

        Usage:
            weather.send(temperature=26.4, humidity=62.1, pressure=1013.2)
        """
        self._validate(fields)
        reading = SensorReading(
            measurement=self.MEASUREMENT,
            device_id=self._device_id,
            tags={
                "device_id": self._device_id,
                "location":  self._location,
                **self._compute_alert_tags(fields),
            },
            fields={k: round(float(v), 4) if isinstance(v, float) else v
                    for k, v in fields.items()},
        )
        self._client._dispatch(reading)
        self._last_reading = reading
        self._count += 1
        log.debug(f"[{self.MEASUREMENT}] Reading #{self._count} dispatched.")
        return reading

    def last(self) -> Optional[SensorReading]:
        """Return the last reading sent."""
        return self._last_reading

    @property
    def count(self) -> int:
        """Total readings sent this session."""
        return self._count

    def field_unit(self, field_name: str) -> str:
        return self.FIELD_UNITS.get(field_name, "")

    # ── Private ───────────────────────────────────────────────────────────────

    def _validate(self, fields: dict) -> None:
        missing = [f for f in self.REQUIRED_FIELDS if f not in fields]
        if missing:
            raise ValueError(
                f"{self.__class__.__name__}.send() missing required fields: "
                f"{missing}. Required: {self.REQUIRED_FIELDS}"
            )
        unknown = [k for k in fields
                   if k not in self.REQUIRED_FIELDS
                   and k not in self.OPTIONAL_FIELDS]
        if unknown:
            log.warning(
                f"{self.__class__.__name__}: unknown fields {unknown} "
                f"will still be sent but are not documented.")

    def _compute_alert_tags(self, fields: dict) -> dict:
        tags = {}
        for field_name, (lo, hi, label) in self.ALERT_THRESHOLDS.items():
            val = fields.get(field_name)
            if val is not None:
                if val >= hi:
                    tags[f"{field_name}_alert"] = f"HIGH_{label}"
                elif val <= lo:
                    tags[f"{field_name}_alert"] = f"LOW_{label}"
                else:
                    tags[f"{field_name}_alert"] = "NORMAL"
        return tags


# ══════════════════════════════════════════════════════════════════════════════
# WEATHER STATION SENSOR  (Project 1)
# ══════════════════════════════════════════════════════════════════════════════

class WeatherStation(BaseSensor):
    """
    Weather Station sensor abstraction for Lab Project 1.

    Sensors modelled:
      • DHT22       — temperature (°C), humidity (%)
      • BMP280      — pressure (hPa), altitude (m)
      • MQ135       — CO2 (ppm), air quality index (0–500)
      • BH1750      — light intensity (lux)
      • Anemometer  — wind_speed (km/h), wind_direction (°)
      • Rain gauge  — rainfall (mm/hr)

    Usage:
        weather = WeatherStation(client)
        weather.send(
            temperature   = 26.4,
            humidity      = 62.1,
            pressure      = 1013.2,
            altitude      = 48.5,
            co2_ppm       = 412.0,
            aqi           = 52.0,
            light_lux     = 8500.0,
            wind_speed    = 12.4,
            wind_direction= 225.0,
            rainfall_mm   = 0.0,
        )
    """

    MEASUREMENT = "weather"

    REQUIRED_FIELDS = ["temperature", "humidity"]

    OPTIONAL_FIELDS = [
        "pressure", "altitude",
        "co2_ppm", "aqi",
        "light_lux",
        "wind_speed", "wind_direction",
        "rainfall_mm",
        "battery_pct", "rssi_dbm",
    ]

    ALERT_THRESHOLDS = {
        # field         : (low_threshold, high_threshold, label)
        "temperature"   : (0.0,   38.0,  "TEMP"),
        "humidity"      : (10.0,  90.0,  "HUM"),
        "co2_ppm"       : (0.0,   1000.0,"CO2"),
        "aqi"           : (0.0,   150.0, "AQI"),
        "wind_speed"    : (0.0,   60.0,  "WIND"),
    }

    FIELD_UNITS = {
        "temperature":    "°C",
        "humidity":       "%",
        "pressure":       "hPa",
        "altitude":       "m",
        "co2_ppm":        "ppm",
        "aqi":            "AQI",
        "light_lux":      "lux",
        "wind_speed":     "km/h",
        "wind_direction": "°",
        "rainfall_mm":    "mm/hr",
        "battery_pct":    "%",
        "rssi_dbm":       "dBm",
    }

    WIND_DIRECTIONS = {
        0: "N", 45: "NE", 90: "E", 135: "SE",
        180: "S", 225: "SW", 270: "W", 315: "NW",
    }

    @staticmethod
    def wind_direction_label(degrees: float) -> str:
        """Convert wind direction in degrees to cardinal label."""
        dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                "S","SSW","SW","WSW","W","WNW","NW","NNW"]
        idx = round(degrees / 22.5) % 16
        return dirs[idx]

    @staticmethod
    def aqi_category(aqi: float) -> str:
        if aqi <= 50:   return "Good"
        if aqi <= 100:  return "Moderate"
        if aqi <= 150:  return "Unhealthy for Sensitive Groups"
        if aqi <= 200:  return "Unhealthy"
        if aqi <= 300:  return "Very Unhealthy"
        return "Hazardous"


# ══════════════════════════════════════════════════════════════════════════════
# SMART HOME SENSOR  (Project 2)
# ══════════════════════════════════════════════════════════════════════════════

class SmartHome(BaseSensor):
    """
    Smart Home sensor abstraction for Lab Project 2.

    Sensors modelled:
      • PIR          — motion (bool), occupancy_duration (s)
      • Relay        — light_state (ON/OFF), relay_state (bool)
      • MQ2          — smoke_ppm (ppm), lpg_ppm (ppm), co_ppm (ppm)
      • Reed switch  — door_open (bool), window_open (bool)
      • Ambient light— ambient_lux (lux), daylight (bool)
      • Sound        — sound_db (dB)
      • Indoor temp  — indoor_temp (°C), indoor_humidity (%)

    Usage:
        home = SmartHome(client, room="LivingRoom")
        home.send(
            motion              = True,
            occupancy_duration  = 0,
            light_state         = "ON",
            relay_state         = True,
            smoke_ppm           = 12.0,
            door_open           = False,
            ambient_lux         = 320.0,
            sound_db            = 42.0,
            indoor_temp         = 24.5,
            indoor_humidity     = 55.0,
        )
    """

    MEASUREMENT = "smarthome"

    REQUIRED_FIELDS = ["motion", "light_state"]

    OPTIONAL_FIELDS = [
        "occupancy_duration",
        "relay_state",
        "smoke_ppm", "lpg_ppm", "co_ppm",
        "door_open", "window_open",
        "ambient_lux", "daylight",
        "sound_db",
        "indoor_temp", "indoor_humidity",
        "battery_pct", "rssi_dbm",
    ]

    ALERT_THRESHOLDS = {
        "smoke_ppm"   : (0.0,   300.0, "SMOKE"),
        "co_ppm"      : (0.0,   50.0,  "CO"),
        "sound_db"    : (0.0,   85.0,  "NOISE"),
        "indoor_temp" : (10.0,  32.0,  "TEMP"),
    }

    FIELD_UNITS = {
        "motion":             "bool",
        "occupancy_duration": "s",
        "light_state":        "ON/OFF",
        "relay_state":        "bool",
        "smoke_ppm":          "ppm",
        "lpg_ppm":            "ppm",
        "co_ppm":             "ppm",
        "door_open":          "bool",
        "window_open":        "bool",
        "ambient_lux":        "lux",
        "daylight":           "bool",
        "sound_db":           "dB",
        "indoor_temp":        "°C",
        "indoor_humidity":    "%",
        "battery_pct":        "%",
        "rssi_dbm":           "dBm",
    }

    def __init__(self, client, room: str = "Room1", **kwargs) -> None:
        super().__init__(client, **kwargs)
        self._room = room
        self._location = room

    def send(self, **fields) -> SensorReading:
        """Adds room tag automatically."""
        reading = super().send(**fields)
        reading.tags["room"] = self._room
        return reading
