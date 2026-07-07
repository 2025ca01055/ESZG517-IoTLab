"""
IoTLab Configuration Manager
Loads, validates, and provides access to iotlab_config.json
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger("iotlab.config")

DEFAULT_CONFIG_PATHS = [
    Path("iotlab_config.json"),
    Path.home() / ".iotlab" / "config.json",
    Path(__file__).parent.parent / "iotlab_config.json",
]


@dataclass
class MQTTConfig:
    broker:    str  = "your-cluster.s2.eu.hivemq.cloud"
    port:      int  = 8883
    username:  str  = "iotlab"
    password:  str  = ""
    tls:       bool = True
    keepalive: int  = 60
    topics:    dict = field(default_factory=lambda: {
        "weather":   "eszg517/lab/weather",
        "smarthome": "eszg517/home",
        "alerts":    "eszg517/alerts",
    })


@dataclass
class InfluxConfig:
    url:    str = ""
    token:  str = ""
    org:    str = ""
    bucket: str = "iotlab"


@dataclass
class DeviceConfig:
    weather_id:   str = "ESZG517_WeatherNode_01"
    smarthome_id: str = "ESZG517_SmartHome_01"
    location:     str = "Lab_Room"


@dataclass
class PublisherConfig:
    interval_seconds: int = 5
    qos:              int = 1


class IoTLabConfig:
    """
    Loads iotlab_config.json and exposes typed sub-configurations.

    Usage:
        cfg = IoTLabConfig()                         # auto-discovers config file
        cfg = IoTLabConfig("/path/to/config.json")  # explicit path
        print(cfg.mqtt.broker)
        print(cfg.influxdb.bucket)
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = self._resolve_path(path)
        self._raw  = {}
        self.mqtt      = MQTTConfig()
        self.influxdb  = InfluxConfig()
        self.device    = DeviceConfig()
        self.publisher = PublisherConfig()
        self._load()

    # ── Public ────────────────────────────────────────────────────────────────

    def reload(self) -> None:
        """Reload config from disk."""
        self._load()

    def validate(self) -> list[str]:
        """
        Returns a list of validation error strings.
        Empty list means config is valid.
        """
        errors = []
        if not self.mqtt.broker or "your-cluster" in self.mqtt.broker:
            errors.append("mqtt.broker is not configured")
        if not self.mqtt.password:
            errors.append("mqtt.password is empty")
        if not self.influxdb.url or "your-region" in self.influxdb.url:
            errors.append("influxdb.url is not configured")
        if not self.influxdb.token or "your-influxdb" in self.influxdb.token:
            errors.append("influxdb.token is not configured")
        if not self.influxdb.org or "your-org" in self.influxdb.org:
            errors.append("influxdb.org is not configured")
        return errors

    def summary(self) -> str:
        lines = [
            "─── IoTLab Configuration ───────────────────────────",
            f"  Config file   : {self._path}",
            f"  MQTT Broker   : {self.mqtt.broker}:{self.mqtt.port}",
            f"  MQTT Username : {self.mqtt.username}",
            f"  MQTT TLS      : {self.mqtt.tls}",
            f"  InfluxDB URL  : {self.influxdb.url}",
            f"  InfluxDB Org  : {self.influxdb.org}",
            f"  InfluxDB Bucket: {self.influxdb.bucket}",
            f"  Device IDs    : {self.device.weather_id} | {self.device.smarthome_id}",
            f"  Publish Every : {self.publisher.interval_seconds}s  QoS={self.publisher.qos}",
            "─────────────────────────────────────────────────────",
        ]
        errors = self.validate()
        if errors:
            lines.append("  ⚠  WARNINGS:")
            for e in errors:
                lines.append(f"     • {e}")
            lines.append("─────────────────────────────────────────────────────")
        return "\n".join(lines)

    # ── Private ───────────────────────────────────────────────────────────────

    def _resolve_path(self, path: Optional[str]) -> Path:
        if path:
            p = Path(path)
            if not p.exists():
                raise FileNotFoundError(f"Config file not found: {p}")
            return p
        for candidate in DEFAULT_CONFIG_PATHS:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "iotlab_config.json not found. "
            "Run 'iotlab init' or create iotlab_config.json in the current folder."
        )

    def _load(self) -> None:
        with open(self._path) as f:
            self._raw = json.load(f)

        def _update(dc, src: dict):
            for k, v in src.items():
                if k.startswith("_"):
                    continue
                if hasattr(dc, k):
                    setattr(dc, k, v)

        _update(self.mqtt,      self._raw.get("mqtt",      {}))
        _update(self.influxdb,  self._raw.get("influxdb",  {}))
        _update(self.device,    self._raw.get("device",    {}))
        _update(self.publisher, self._raw.get("publisher", {}))
        log.info(f"Config loaded from {self._path}")
