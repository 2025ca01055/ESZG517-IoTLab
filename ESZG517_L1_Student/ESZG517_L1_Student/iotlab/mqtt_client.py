"""
IoTLab MQTT Client
Handles subscribe/publish for both emulator users and physical ESP32 users.
The workflow is identical for both:
  ESP32 / Emulator  →  MQTT (HiveMQ Cloud)  →  IoTLabMQTTClient (subscribe)  →  InfluxDB
"""

from __future__ import annotations

import json
import logging
import ssl
import time
from threading import Event, Thread
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from .config  import IoTLabConfig
from .sensor  import SensorReading

log = logging.getLogger("iotlab.mqtt")

# Callback type: fn(topic: str, reading: SensorReading) -> None
MessageCallback = Callable[[str, SensorReading], None]


class IoTLabMQTTClient:
    """
    Manages MQTT connection, subscription, and publication.

    Works identically for:
      • Emulator users (emulator publishes → this client subscribes)
      • ESP32 users    (ESP32 publishes    → this client subscribes)
      • Test publisher (this client publishes test data)

    Usage:
        client = IoTLabMQTTClient(config)
        client.on_message(callback_fn)
        client.connect()
        client.subscribe("eszg517/lab/weather")
        # ... do work ...
        client.disconnect()
    """

    def __init__(self, config: IoTLabConfig) -> None:
        self._cfg       = config
        self._client:   Optional[mqtt.Client] = None
        self._connected = Event()
        self._callbacks: list[MessageCallback] = []
        self._subscriptions: list[tuple[str, int]] = []
        self._stats = {
            "published":   0,
            "received":    0,
            "errors":      0,
            "connect_ts":  None,
        }

    # ── Connection ────────────────────────────────────────────────────────────

    def connect(self, timeout: float = 10.0) -> bool:
        """
        Connect to MQTT broker. Blocks until connected or timeout.
        Returns True on success, raises on failure.
        """
        cfg = self._cfg.mqtt
        self._client = mqtt.Client(
            client_id=f"IoTLab_Framework_{int(time.time())}",
            protocol=mqtt.MQTTv311,
        )
        self._client.username_pw_set(cfg.username, cfg.password)
        if cfg.tls:
            self._client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self._client.on_connect    = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message    = self._on_message

        log.info(f"Connecting to {cfg.broker}:{cfg.port} ...")
        self._client.connect(cfg.broker, cfg.port, keepalive=cfg.keepalive)
        self._client.loop_start()

        if not self._connected.wait(timeout):
            self._client.loop_stop()
            raise TimeoutError(
                f"Could not connect to {cfg.broker}:{cfg.port} "
                f"within {timeout}s. Check broker URL and credentials."
            )
        return True

    def disconnect(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected.clear()
            log.info("MQTT disconnected.")

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    # ── Subscriptions ─────────────────────────────────────────────────────────

    def subscribe(self, topic: str, qos: int = 1) -> None:
        """Subscribe to a topic. Wildcard # and + supported."""
        self._subscriptions.append((topic, qos))
        if self.is_connected:
            self._client.subscribe(topic, qos)
            log.info(f"Subscribed to {topic} (QoS {qos})")

    def subscribe_all(self) -> None:
        """Subscribe to all configured topics (weather + smarthome + alerts)."""
        topics = self._cfg.mqtt.topics
        self.subscribe(f"{topics['weather']}/#")
        self.subscribe(f"{topics['smarthome']}/#")
        self.subscribe(f"{topics['alerts']}/#")

    def on_message(self, callback: MessageCallback) -> None:
        """Register a callback: fn(topic, SensorReading) -> None"""
        self._callbacks.append(callback)

    # ── Publishing ────────────────────────────────────────────────────────────

    def publish(self, topic: str, payload: str,
                qos: int = 1, retain: bool = False) -> bool:
        """Publish a raw string payload."""
        if not self.is_connected:
            log.error("Cannot publish: not connected.")
            return False
        result = self._client.publish(topic, payload, qos=qos, retain=retain)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self._stats["published"] += 1
            log.debug(f"PUB → {topic}: {payload[:80]}")
            return True
        self._stats["errors"] += 1
        log.error(f"Publish failed on {topic}: rc={result.rc}")
        return False

    def publish_reading(self, reading: SensorReading,
                        topic: Optional[str] = None,
                        retain: bool = False) -> bool:
        """Publish a SensorReading object."""
        if topic is None:
            base = self._cfg.mqtt.topics.get(reading.measurement,
                                             f"eszg517/{reading.measurement}")
            topic = f"{base}/{reading.device_id}"
        return self.publish(topic, reading.to_json(),
                            qos=self._cfg.publisher.qos, retain=retain)

    # ── Statistics ────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        s = dict(self._stats)
        if s["connect_ts"]:
            s["uptime_s"] = int(time.time() - s["connect_ts"])
        return s

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self._connected.set()
            self._stats["connect_ts"] = time.time()
            log.info("MQTT connected.")
            for topic, qos in self._subscriptions:
                client.subscribe(topic, qos)
        else:
            codes = {4: "Bad credentials", 5: "Not authorised",
                     3: "Server unavailable", 2: "ID rejected"}
            log.error(f"MQTT connect failed: {codes.get(rc, rc)}")

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._connected.clear()
        log.warning(f"MQTT disconnected (rc={rc})")

    def _on_message(self, client, userdata, msg) -> None:
        self._stats["received"] += 1
        try:
            reading = SensorReading.from_json(msg.payload.decode())
        except Exception:
            # Fallback: wrap raw payload in a generic SensorReading
            reading = SensorReading(
                measurement="raw",
                device_id="unknown",
                fields={"raw": msg.payload.decode()},
            )
        for cb in self._callbacks:
            try:
                cb(msg.topic, reading)
            except Exception as e:
                log.error(f"Callback error: {e}")
