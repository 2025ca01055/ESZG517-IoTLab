"""
IoTLab InfluxDB Writer
Writes SensorReading objects to InfluxDB using the Flux write API.
"""

from __future__ import annotations

import logging
import time
from typing import Optional, Union

log = logging.getLogger("iotlab.writer")

try:
    from influxdb_client import InfluxDBClient, Point, WritePrecision
    from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
    _INFLUX_AVAILABLE = True
except ImportError:
    _INFLUX_AVAILABLE = False
    log.warning(
        "influxdb-client not installed. "
        "Run: pip install influxdb-client"
    )

from .config import IoTLabConfig
from .sensor import SensorReading


class IoTLabWriter:
    """
    Writes SensorReading objects to InfluxDB Cloud.

    Usage:
        writer = IoTLabWriter(config)
        writer.connect()
        writer.write(reading)
        writer.disconnect()

    Or as context manager:
        with IoTLabWriter(config) as writer:
            writer.write(reading)
    """

    def __init__(self, config: IoTLabConfig,
                 async_write: bool = False) -> None:
        if not _INFLUX_AVAILABLE:
            raise ImportError(
                "influxdb-client required. Run: pip install influxdb-client")
        self._cfg         = config
        self._async       = async_write
        self._client:     Optional[InfluxDBClient] = None
        self._write_api   = None
        self._stats = {"written": 0, "errors": 0, "last_write_ts": None}

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        cfg = self._cfg.influxdb
        self._client   = InfluxDBClient(
            url=cfg.url, token=cfg.token, org=cfg.org)
        write_options = ASYNCHRONOUS if self._async else SYNCHRONOUS
        self._write_api = self._client.write_api(write_options=write_options)
        log.info(f"InfluxDB writer connected: {cfg.url} → {cfg.bucket}")

    def disconnect(self) -> None:
        if self._write_api:
            self._write_api.close()
        if self._client:
            self._client.close()
        log.info("InfluxDB writer disconnected.")

    def __enter__(self):  self.connect();    return self
    def __exit__(self, *_): self.disconnect()

    # ── Write ─────────────────────────────────────────────────────────────────

    def write(self, reading: SensorReading) -> bool:
        """Write a single SensorReading to InfluxDB."""
        try:
            point = self._reading_to_point(reading)
            self._write_api.write(
                bucket=self._cfg.influxdb.bucket,
                record=point,
            )
            self._stats["written"]       += 1
            self._stats["last_write_ts"] = time.time()
            log.debug(f"Written: {reading.measurement}/{reading.device_id}")
            return True
        except Exception as e:
            self._stats["errors"] += 1
            log.error(f"InfluxDB write error: {e}")
            return False

    def write_batch(self, readings: list[SensorReading]) -> int:
        """Write multiple readings. Returns count of successful writes."""
        points = []
        for r in readings:
            try:
                points.append(self._reading_to_point(r))
            except Exception as e:
                log.error(f"Point conversion error: {e}")
        if not points:
            return 0
        try:
            self._write_api.write(
                bucket=self._cfg.influxdb.bucket,
                record=points,
            )
            self._stats["written"]       += len(points)
            self._stats["last_write_ts"] = time.time()
            return len(points)
        except Exception as e:
            self._stats["errors"] += 1
            log.error(f"InfluxDB batch write error: {e}")
            return 0

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    @staticmethod
    def _reading_to_point(reading: SensorReading) -> "Point":
        point = (Point(reading.measurement)
                 .time(reading.timestamp * 1_000_000_000, "ns"))
        for k, v in reading.tags.items():
            point = point.tag(k, str(v))
        for k, v in reading.fields.items():
            if isinstance(v, bool):
                point = point.field(k, v)
            elif isinstance(v, (int, float)):
                point = point.field(k, float(v))
            else:
                point = point.field(k, str(v))
        return point
