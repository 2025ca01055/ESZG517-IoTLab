"""
IoTLab Unified Client
Single entry point that wires together config, MQTT, and InfluxDB.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from .config      import IoTLabConfig
from .mqtt_client import IoTLabMQTTClient
from .db_writer   import IoTLabWriter
from .db_reader   import IoTLabReader
from .sensor      import SensorReading

log = logging.getLogger("iotlab.client")


class IoTLabClient:
    """
    Unified IoTLab client — the only object most students need to import.

    Wires together:
      • IoTLabConfig   — loads iotlab_config.json
      • IoTLabMQTTClient — MQTT pub/sub (works for emulator AND ESP32)
      • IoTLabWriter   — writes sensor readings to InfluxDB
      • IoTLabReader   — queries InfluxDB, returns DataFrames

    Usage (publisher mode — emulator or test scripts):
        from iotlab import IoTLabClient, WeatherStation

        client  = IoTLabClient()
        client.connect()

        weather = WeatherStation(client)
        weather.send(temperature=26.4, humidity=62.1, pressure=1013.2)

        client.disconnect()

    Usage (subscriber mode — listen and store):
        client = IoTLabClient()
        client.connect(subscribe=True)   # subscribes + writes all incoming to InfluxDB
        client.loop_forever()            # blocks until Ctrl+C

    Usage (reader mode — data analysis):
        client = IoTLabClient()
        df = client.reader.weather(hours=2)
        print(df.describe())
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config = IoTLabConfig(config_path)
        self._mqtt:   Optional[IoTLabMQTTClient] = None
        self._writer: Optional[IoTLabWriter]     = None
        self._reader: Optional[IoTLabReader]     = None

    # ── Connection ────────────────────────────────────────────────────────────

    def connect(self, subscribe: bool = False,
                write_db: bool = True) -> "IoTLabClient":
        """
        Connect to MQTT and optionally InfluxDB.

        Args:
            subscribe : if True, subscribe to all configured topics
                        and auto-write incoming messages to InfluxDB
            write_db  : if True, connect the InfluxDB writer

        Returns self for chaining:
            client.connect(subscribe=True).loop_forever()
        """
        errors = self.config.validate()
        if errors:
            log.warning("Config has issues:")
            for e in errors:
                log.warning(f"  • {e}")

        # MQTT
        self._mqtt = IoTLabMQTTClient(self.config)
        self._mqtt.connect()

        # InfluxDB writer
        if write_db:
            self._writer = IoTLabWriter(self.config)
            self._writer.connect()

        # Auto-subscribe and auto-write pipeline
        if subscribe:
            self._mqtt.subscribe_all()
            if self._writer:
                self._mqtt.on_message(self._auto_write_callback)
            log.info("Subscriber + writer pipeline active.")

        log.info("IoTLabClient connected.")
        return self

    def disconnect(self) -> None:
        if self._mqtt:
            self._mqtt.disconnect()
        if self._writer:
            self._writer.disconnect()
        if self._reader:
            self._reader.disconnect()
        log.info("IoTLabClient disconnected.")

    def loop_forever(self) -> None:
        """
        Block forever, processing incoming MQTT messages.
        Exit with Ctrl+C.
        """
        log.info("Listening for sensor data. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Stopping...")
            self.disconnect()

    # ── Writer / Reader access ────────────────────────────────────────────────

    @property
    def reader(self) -> IoTLabReader:
        """Lazy-init InfluxDB reader."""
        if self._reader is None:
            self._reader = IoTLabReader(self.config)
            self._reader.connect()
        return self._reader

    # ── Internal dispatch (called by sensor.BaseSensor.send()) ───────────────

    def _dispatch(self, reading: SensorReading) -> None:
        """
        Called by WeatherStation.send() / SmartHome.send().
        Publishes to MQTT and writes to InfluxDB.
        """
        if self._mqtt and self._mqtt.is_connected:
            self._mqtt.publish_reading(reading)
        if self._writer:
            self._writer.write(reading)

    # ── Auto-write callback ───────────────────────────────────────────────────

    def _auto_write_callback(self, topic: str,
                             reading: SensorReading) -> None:
        """Write every received MQTT message to InfluxDB."""
        if self._writer:
            ok = self._writer.write(reading)
            if ok:
                log.info(
                    f"[{topic}] Written: "
                    f"{reading.measurement}/{reading.device_id} "
                    f"fields={list(reading.fields.keys())}"
                )

    # ── Stats ─────────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        return {
            "mqtt":    self._mqtt.stats    if self._mqtt    else {},
            "writer":  self._writer.stats  if self._writer  else {},
        }
