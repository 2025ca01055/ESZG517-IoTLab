"""
IoTLab InfluxDB Reader
Queries InfluxDB and returns pandas DataFrames for analysis and ML.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

log = logging.getLogger("iotlab.reader")

try:
    from influxdb_client import InfluxDBClient
    _INFLUX_AVAILABLE = True
except ImportError:
    _INFLUX_AVAILABLE = False

try:
    import pandas as pd
    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False
    log.warning("pandas not installed. Run: pip install pandas")

from .config import IoTLabConfig


class IoTLabReader:
    """
    Queries InfluxDB and returns pandas DataFrames.

    Usage:
        reader = IoTLabReader(config)
        reader.connect()

        # Get last hour of weather data
        df = reader.weather(hours=1)
        print(df[["temperature","humidity","co2_ppm"]].describe())

        # Get anomaly candidates (temperature > 38°C)
        alerts = reader.alerts(measurement="weather", field="temperature", threshold=38.0)

        # Export to CSV for ML Lab
        reader.export_csv("weather_1h.csv", measurement="weather", hours=1)

        reader.disconnect()

    Or as context manager:
        with IoTLabReader(config) as reader:
            df = reader.weather(hours=1)
    """

    def __init__(self, config: IoTLabConfig) -> None:
        if not _INFLUX_AVAILABLE:
            raise ImportError(
                "influxdb-client required. Run: pip install influxdb-client")
        self._cfg    = config
        self._client: Optional[InfluxDBClient] = None
        self._query_api = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        cfg = self._cfg.influxdb
        self._client    = InfluxDBClient(
            url=cfg.url, token=cfg.token, org=cfg.org)
        self._query_api = self._client.query_api()
        log.info(f"InfluxDB reader connected: {cfg.url}")

    def disconnect(self) -> None:
        if self._client:
            self._client.close()
        log.info("InfluxDB reader disconnected.")

    def __enter__(self):  self.connect();    return self
    def __exit__(self, *_): self.disconnect()

    # ── High-level query methods ──────────────────────────────────────────────

    def weather(self, hours: float = 1.0,
                device_id: Optional[str] = None) -> "pd.DataFrame":
        """
        Return weather sensor readings for the last N hours.

        Returns DataFrame with columns:
            _time, device_id, temperature, humidity, pressure,
            altitude, co2_ppm, aqi, light_lux, wind_speed,
            wind_direction, rainfall_mm, battery_pct, rssi_dbm
        """
        return self._query_measurement("weather", hours, device_id)

    def smarthome(self, hours: float = 1.0,
                  device_id: Optional[str] = None,
                  room: Optional[str] = None) -> "pd.DataFrame":
        """
        Return smart home sensor readings for the last N hours.

        Returns DataFrame with columns:
            _time, device_id, room, motion, light_state,
            smoke_ppm, door_open, ambient_lux, sound_db,
            indoor_temp, indoor_humidity, ...
        """
        df = self._query_measurement("smarthome", hours, device_id)
        if room and not df.empty and "room" in df.columns:
            df = df[df["room"] == room]
        return df

    def alerts(self, measurement: str, field: str,
               threshold: float, operator: str = ">",
               hours: float = 24.0) -> "pd.DataFrame":
        """
        Return readings where field crosses threshold.

        Args:
            measurement : "weather" or "smarthome"
            field       : e.g. "temperature", "co2_ppm", "smoke_ppm"
            threshold   : numeric threshold value
            operator    : ">", "<", ">=", "<="
            hours       : look-back window

        Returns filtered DataFrame sorted by time descending.
        """
        df = self._query_measurement(measurement, hours)
        if df.empty or field not in df.columns:
            return df
        op_map = {
            ">":  df[field] > threshold,
            "<":  df[field] < threshold,
            ">=": df[field] >= threshold,
            "<=": df[field] <= threshold,
        }
        mask = op_map.get(operator, df[field] > threshold)
        return df[mask].sort_values("_time", ascending=False).reset_index(drop=True)

    def latest(self, measurement: str,
               device_id: Optional[str] = None) -> dict:
        """
        Return the single most recent reading as a plain dict.
        Useful for status checks and CLI display.
        """
        df = self._query_measurement(measurement, hours=0.5, device_id=device_id)
        if df.empty:
            return {}
        row = df.iloc[-1]
        return {col: row[col] for col in df.columns if not col.startswith("_")}

    def statistics(self, measurement: str,
                   hours: float = 24.0) -> "pd.DataFrame":
        """
        Return min, max, mean, std for all numeric fields
        over the given window. Useful for lab reports.
        """
        df = self._query_measurement(measurement, hours)
        if df.empty:
            return df
        numeric = df.select_dtypes(include="number")
        return numeric.describe().T[["min", "max", "mean", "std"]].round(3)

    def export_csv(self, filepath: str,
                   measurement: str = "weather",
                   hours: float = 1.0) -> int:
        """
        Export data to CSV. Returns number of rows written.

        Usage:
            rows = reader.export_csv("lab_data.csv", measurement="weather", hours=2)
            print(f"Exported {rows} rows to lab_data.csv")
        """
        if not _PANDAS_AVAILABLE:
            raise ImportError("pandas required for CSV export.")
        df = self._query_measurement(measurement, hours)
        if df.empty:
            log.warning("No data to export.")
            return 0
        df.to_csv(filepath, index=False)
        log.info(f"Exported {len(df)} rows to {filepath}")
        return len(df)

    # ── Flux query builder ────────────────────────────────────────────────────

    def _query_measurement(self, measurement: str,
                           hours: float,
                           device_id: Optional[str] = None) -> "pd.DataFrame":
        if not _PANDAS_AVAILABLE:
            raise ImportError("pandas required. Run: pip install pandas")
        bucket = self._cfg.influxdb.bucket
        start = f"-{int(hours)}h" if hours >= 1 else f"-{int(hours * 60)}m"
        device_filter = (
            f'|> filter(fn: (r) => r["device_id"] == "{device_id}")'
            if device_id else ""
        )
        flux = f"""
from(bucket: "{bucket}")
  |> range(start: {start})
  |> filter(fn: (r) => r["_measurement"] == "{measurement}")
  {device_filter}
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"])
"""
        try:
            tables = self._query_api.query(flux)
            records = []
            for table in tables:
                for record in table.records:
                    records.append(record.values)
            if not records:
                return pd.DataFrame()
            df = pd.DataFrame(records)
            # Drop internal InfluxDB columns
            drop_cols = [c for c in df.columns
                         if c.startswith("_") and c != "_time"
                         or c in ("result", "table")]
            df = df.drop(columns=[c for c in drop_cols if c in df.columns])
            if "_time" in df.columns:
                df = df.rename(columns={"_time": "timestamp"})
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df.reset_index(drop=True)
        except Exception as e:
            log.error(f"Query error for {measurement}: {e}")
            return pd.DataFrame()
