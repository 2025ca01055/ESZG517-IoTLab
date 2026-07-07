"""
IoTLab Test Publisher
Publishes realistic simulated sensor data to MQTT.
Works identically to a physical ESP32 from the framework's perspective.

Usage:
    python -m iotlab.publisher --mode weather --interval 5
    python -m iotlab.publisher --mode smarthome --interval 3
    python -m iotlab.publisher --mode both --interval 5
    python -m iotlab.publisher --mode weather --scenario fire_alert
"""

from __future__ import annotations

import argparse
import logging
import math
import random
import time
from typing import Optional

from .client import IoTLabClient
from .sensor import WeatherStation, SmartHome, SensorReading

log = logging.getLogger("iotlab.publisher")


# ══════════════════════════════════════════════════════════════════════════════
# REALISTIC DATA GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

class WeatherDataGenerator:
    """
    Generates realistic weather sensor readings using sinusoidal drift
    and Gaussian noise — same model as the emulator app.
    """

    SCENARIOS = {
        "normal":      {"temp": (22.0, 30.0), "hum": (50.0, 80.0),
                        "co2": (380.0, 450.0), "aqi": (20.0, 60.0)},
        "heatwave":    {"temp": (30.0, 38.0), "hum": (20.0, 50.0),
                        "co2": (400.0, 480.0), "aqi": (80.0, 120.0)},
        "fire_alert":  {"temp": (38.0, 50.0), "hum": (5.0,  25.0),
                        "co2": (500.0, 800.0), "aqi": (150.0, 300.0)},
        "night":       {"temp": (18.0, 24.0), "hum": (60.0, 90.0),
                        "co2": (370.0, 420.0), "aqi": (10.0, 40.0)},
    }

    def __init__(self, scenario: str = "normal") -> None:
        self._scenario = scenario.lower().replace(" ", "_")
        self._phase    = 0.0
        self._base_pressure = random.uniform(1005.0, 1020.0)
        self._rainfall_acc  = 0.0

    def next(self) -> dict:
        self._phase += 0.12
        s = self.SCENARIOS.get(self._scenario,
                               self.SCENARIOS["normal"])

        def drift(lo, hi, noise_sd):
            center = (lo + hi) / 2
            amp    = (hi - lo) / 2 * 0.6
            return max(lo, min(hi,
                center + amp * math.sin(self._phase) + random.gauss(0, noise_sd)))

        temp     = round(drift(s["temp"][0], s["temp"][1], 0.4), 2)
        hum      = round(drift(s["hum"][0],  s["hum"][1],  1.0), 2)
        co2      = round(drift(s["co2"][0],  s["co2"][1],  10.0), 1)
        aqi      = round(drift(s["aqi"][0],  s["aqi"][1],  5.0), 1)

        pressure  = round(self._base_pressure + random.gauss(0, 0.3), 2)
        altitude  = round(44330 * (1 - (pressure / 1013.25) ** 0.1903), 1)
        light     = round(max(0, random.gauss(8000, 2000)), 1)
        wind_spd  = round(max(0, random.gauss(12, 5)), 1)
        wind_dir  = round((self._phase * 30 + random.gauss(0, 10)) % 360, 1)
        rainfall  = round(max(0, random.gauss(0, 0.5))
                          if self._scenario != "fire_alert" else 0.0, 2)
        battery   = round(random.uniform(72.0, 98.0), 1)
        rssi      = round(random.uniform(-75.0, -45.0), 1)

        return dict(
            temperature    = temp,
            humidity       = hum,
            pressure       = pressure,
            altitude       = altitude,
            co2_ppm        = co2,
            aqi            = aqi,
            light_lux      = light,
            wind_speed     = wind_spd,
            wind_direction = wind_dir,
            rainfall_mm    = rainfall,
            battery_pct    = battery,
            rssi_dbm       = rssi,
        )


class SmartHomeDataGenerator:
    """Generates realistic smart home sensor readings."""

    def __init__(self, motion_freq: str = "normal") -> None:
        self._freq_map = {"rare": (20, 60), "normal": (8, 20), "frequent": (2, 6)}
        self._freq     = self._freq_map.get(motion_freq, (8, 20))
        self._next_motion_ts = time.time() + random.uniform(*self._freq)
        self._light_state    = "OFF"
        self._light_off_ts   = 0.0
        self._light_timeout  = 30
        self._motion_count   = 0
        self._phase          = 0.0
        self._door_state     = False
        self._window_state   = False

    def next(self) -> dict:
        self._phase += 0.1
        now = time.time()

        # Motion logic
        motion = False
        if now >= self._next_motion_ts:
            motion = True
            self._motion_count += 1
            self._light_state   = "ON"
            self._light_off_ts  = now + self._light_timeout
            self._next_motion_ts = now + random.uniform(*self._freq)

        if self._light_state == "ON" and now >= self._light_off_ts:
            self._light_state = "OFF"

        # Occasional door/window toggle
        if random.random() < 0.02:
            self._door_state = not self._door_state
        if random.random() < 0.01:
            self._window_state = not self._window_state

        # Smoke — rare spike
        smoke = round(max(0, random.gauss(8, 3) +
                          (random.gauss(200, 50) if random.random() < 0.01 else 0)), 1)

        ambient = round(max(0, 500 + 300 * math.sin(self._phase) + random.gauss(0, 50)), 1)
        sound   = round(max(20, random.gauss(42, 8)), 1)
        i_temp  = round(22.0 + 3 * math.sin(self._phase * 0.3) + random.gauss(0, 0.3), 2)
        i_hum   = round(max(30, min(70, 52 + random.gauss(0, 3))), 1)
        battery = round(random.uniform(80.0, 99.0), 1)
        rssi    = round(random.uniform(-65.0, -40.0), 1)

        return dict(
            motion              = motion,
            occupancy_duration  = self._motion_count * 30,
            light_state         = self._light_state,
            relay_state         = self._light_state == "ON",
            smoke_ppm           = smoke,
            lpg_ppm             = round(max(0, random.gauss(5, 2)), 1),
            co_ppm              = round(max(0, random.gauss(3, 1)), 1),
            door_open           = self._door_state,
            window_open         = self._window_state,
            ambient_lux         = ambient,
            daylight            = ambient > 200,
            sound_db            = sound,
            indoor_temp         = i_temp,
            indoor_humidity     = i_hum,
            battery_pct         = battery,
            rssi_dbm            = rssi,
        )


# ══════════════════════════════════════════════════════════════════════════════
# PUBLISHER
# ══════════════════════════════════════════════════════════════════════════════

def run_publisher(mode:     str  = "both",
                  interval: int  = 5,
                  scenario: str  = "normal",
                  config:   str  = None,
                  count:    int  = 0) -> None:
    """
    Run the test publisher.

    Args:
        mode     : "weather", "smarthome", or "both"
        interval : seconds between publishes
        scenario : weather scenario ("normal","heatwave","fire_alert","night")
        config   : path to iotlab_config.json (None = auto-discover)
        count    : number of readings to send (0 = infinite)
    """
    client = IoTLabClient(config)
    client.connect(subscribe=False, write_db=True)

    weather_gen = WeatherDataGenerator(scenario) if mode in ("weather", "both") else None
    smarthome_gen = SmartHomeDataGenerator()     if mode in ("smarthome", "both") else None

    weather_sensor  = WeatherStation(client) if weather_gen   else None
    smarthome_sensor = SmartHome(client)     if smarthome_gen else None

    sent = 0
    log.info(
        f"Publisher started: mode={mode}, scenario={scenario}, "
        f"interval={interval}s. Press Ctrl+C to stop.")
    print(client.config.summary())

    try:
        while count == 0 or sent < count:
            ts_start = time.time()

            if weather_sensor and weather_gen:
                data = weather_gen.next()
                weather_sensor.send(**data)
                print(f"[WEATHER] T={data['temperature']}°C  "
                      f"H={data['humidity']}%  "
                      f"CO2={data['co2_ppm']}ppm  "
                      f"AQI={data['aqi']}  "
                      f"Wind={data['wind_speed']}km/h")

            if smarthome_sensor and smarthome_gen:
                data = smarthome_gen.next()
                smarthome_sensor.send(**data)
                print(f"[SMARTHOME] Motion={'YES' if data['motion'] else 'no'}  "
                      f"Light={data['light_state']}  "
                      f"Smoke={data['smoke_ppm']}ppm  "
                      f"Sound={data['sound_db']}dB  "
                      f"Temp={data['indoor_temp']}°C")

            sent += 1
            elapsed = time.time() - ts_start
            sleep_t = max(0, interval - elapsed)
            time.sleep(sleep_t)

    except KeyboardInterrupt:
        print(f"\nPublisher stopped. Total readings sent: {sent}")
    finally:
        stats = client.stats
        print(f"MQTT published : {stats['mqtt'].get('published', 0)}")
        print(f"DB written     : {stats['writer'].get('written', 0)}")
        client.disconnect()


# ── CLI entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="IoTLab Test Publisher — ESZG517",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m iotlab.publisher --mode weather --scenario normal
  python -m iotlab.publisher --mode smarthome --interval 3
  python -m iotlab.publisher --mode both --scenario fire_alert --count 50
        """
    )
    parser.add_argument("--mode",     default="both",
                        choices=["weather", "smarthome", "both"])
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--scenario", default="normal",
                        choices=["normal", "heatwave", "fire_alert", "night"])
    parser.add_argument("--config",   default=None)
    parser.add_argument("--count",    type=int, default=0,
                        help="Number of readings to send (0=infinite)")
    args = parser.parse_args()
    run_publisher(
        mode=args.mode, interval=args.interval,
        scenario=args.scenario, config=args.config,
        count=args.count,
    )


if __name__ == "__main__":
    main()
