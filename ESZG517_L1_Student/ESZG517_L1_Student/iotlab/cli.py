"""
IoTLab CLI — ESZG517
Command-line interface for the IoTLab framework.

Commands:
    iotlab status              — show config + connection status
    iotlab read weather        — print last 10 weather readings
    iotlab read smarthome      — print last 10 smart home readings
    iotlab stats weather 1     — statistics for last 1 hour
    iotlab export weather 2    — export last 2 hours to CSV
    iotlab publish weather     — start test publisher (weather only)
    iotlab listen              — subscribe and log all incoming messages

Run:
    python -m iotlab.cli <command> [args]
    python -m iotlab <command> [args]     (if __main__.py is present)
"""

from __future__ import annotations

import argparse
import sys
import time
import logging
from typing import Optional

log = logging.getLogger("iotlab.cli")


def _banner() -> str:
    return (
        "\n╔══════════════════════════════════════════════╗\n"
        "║   IoTLab CLI  —  ESZG517 IoT Virtual Lab     ║\n"
        "║   BITS Pilani · Work Integrated Learning     ║\n"
        "╚══════════════════════════════════════════════╝\n"
    )


def cmd_status(config_path: Optional[str]) -> None:
    """Print configuration summary and test connectivity."""
    from .config import IoTLabConfig
    try:
        cfg = IoTLabConfig(config_path)
        print(_banner())
        print(cfg.summary())

        # Test MQTT
        print("\nTesting MQTT connection...")
        from .mqtt_client import IoTLabMQTTClient
        mqtt = IoTLabMQTTClient(cfg)
        try:
            mqtt.connect(timeout=8.0)
            s = mqtt.stats
            print(f"  ✓  MQTT connected to {cfg.mqtt.broker}:{cfg.mqtt.port}")
            mqtt.disconnect()
        except Exception as e:
            print(f"  ✗  MQTT error: {e}")

        # Test InfluxDB
        print("Testing InfluxDB connection...")
        try:
            from influxdb_client import InfluxDBClient
            c = InfluxDBClient(url=cfg.influxdb.url, token=cfg.influxdb.token,
                               org=cfg.influxdb.org)
            health = c.health()
            print(f"  ✓  InfluxDB reachable: {health.status}")
            c.close()
        except Exception as e:
            print(f"  ✗  InfluxDB error: {e}")

    except FileNotFoundError as e:
        print(f"  ✗  {e}")
        sys.exit(1)


def cmd_read(measurement: str, hours: float,
             config_path: Optional[str]) -> None:
    """Print recent readings from InfluxDB."""
    from .config    import IoTLabConfig
    from .db_reader import IoTLabReader
    try:
        import pandas as pd
    except ImportError:
        print("pandas required: pip install pandas")
        sys.exit(1)

    print(_banner())
    cfg    = IoTLabConfig(config_path)
    reader = IoTLabReader(cfg)
    reader.connect()

    if measurement == "weather":
        df = reader.weather(hours=hours)
    else:
        df = reader.smarthome(hours=hours)

    if df.empty:
        print(f"No {measurement} data found in the last {hours}h.")
        print("Make sure the emulator or publisher is running and connected.")
        reader.disconnect()
        return

    # Print last 10 rows nicely
    cols = [c for c in df.columns
            if c not in ("timestamp",) and not c.endswith("_alert")]
    print(f"\n─── Last {min(10, len(df))} {measurement} readings "
          f"(last {hours}h, total {len(df)} rows) ───")

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 140)
    pd.set_option("display.float_format", "{:.2f}".format)

    display_df = df[["timestamp"] + [c for c in cols if c in df.columns]].tail(10)
    print(display_df.to_string(index=False))
    reader.disconnect()


def cmd_stats(measurement: str, hours: float,
              config_path: Optional[str]) -> None:
    """Print statistics for a measurement."""
    from .config    import IoTLabConfig
    from .db_reader import IoTLabReader
    try:
        import pandas as pd
    except ImportError:
        print("pandas required: pip install pandas")
        sys.exit(1)

    print(_banner())
    cfg    = IoTLabConfig(config_path)
    reader = IoTLabReader(cfg)
    reader.connect()
    stats  = reader.statistics(measurement, hours)
    if stats.empty:
        print(f"No data for {measurement} in last {hours}h.")
    else:
        print(f"\n─── {measurement.upper()} Statistics — last {hours}h ───")
        pd.set_option("display.float_format", "{:.3f}".format)
        print(stats.to_string())
    reader.disconnect()


def cmd_export(measurement: str, hours: float,
               output: Optional[str], config_path: Optional[str]) -> None:
    """Export data to CSV."""
    from .config    import IoTLabConfig
    from .db_reader import IoTLabReader

    print(_banner())
    cfg      = IoTLabConfig(config_path)
    reader   = IoTLabReader(cfg)
    reader.connect()
    filename = output or f"{measurement}_{int(time.time())}.csv"
    rows     = reader.export_csv(filename, measurement=measurement, hours=hours)
    if rows:
        print(f"✓  Exported {rows} rows → {filename}")
    else:
        print("No data exported.")
    reader.disconnect()


def cmd_listen(config_path: Optional[str]) -> None:
    """Subscribe to all topics and log to console + InfluxDB."""
    from .client import IoTLabClient
    print(_banner())
    print("Subscribing to all topics. Press Ctrl+C to stop.\n")
    client = IoTLabClient(config_path)
    client.connect(subscribe=True, write_db=True)
    client.loop_forever()


def cmd_publish(mode: str, scenario: str,
                interval: int, config_path: Optional[str]) -> None:
    """Run test publisher."""
    from .publisher import run_publisher
    print(_banner())
    run_publisher(mode=mode, scenario=scenario,
                  interval=interval, config=config_path)


# ══════════════════════════════════════════════════════════════════════════════
# ARGUMENT PARSER
# ══════════════════════════════════════════════════════════════════════════════

def main():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s"
    )

    parser = argparse.ArgumentParser(
        prog="iotlab",
        description="IoTLab CLI — ESZG517 IoT Virtual Lab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands and examples:
  iotlab status
      Check config, test MQTT + InfluxDB connectivity.

  iotlab read weather [--hours 1]
      Print last N hours of weather readings.

  iotlab read smarthome [--hours 1]
      Print last N hours of smart home readings.

  iotlab stats weather [--hours 24]
      Print min/max/mean/std statistics.

  iotlab export weather [--hours 2] [--output lab1_data.csv]
      Export data to CSV (for ML lab).

  iotlab publish [--mode weather] [--scenario fire_alert] [--interval 5]
      Publish test sensor data (for students without hardware).

  iotlab listen
      Subscribe to all topics, write everything to InfluxDB.

  iotlab init
      Create a default iotlab_config.json in current folder.
        """
    )
    parser.add_argument("--config", default=None,
                        help="Path to iotlab_config.json")
    sub = parser.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="Test config and connectivity")

    # read
    p_read = sub.add_parser("read", help="Print recent readings")
    p_read.add_argument("measurement",
                        choices=["weather", "smarthome"])
    p_read.add_argument("--hours", type=float, default=1.0)

    # stats
    p_stats = sub.add_parser("stats", help="Print statistics")
    p_stats.add_argument("measurement",
                         choices=["weather", "smarthome"])
    p_stats.add_argument("--hours", type=float, default=24.0)

    # export
    p_export = sub.add_parser("export", help="Export data to CSV")
    p_export.add_argument("measurement",
                          choices=["weather", "smarthome"])
    p_export.add_argument("--hours",  type=float, default=2.0)
    p_export.add_argument("--output", default=None)

    # publish
    p_pub = sub.add_parser("publish", help="Run test publisher")
    p_pub.add_argument("--mode",     default="both",
                       choices=["weather", "smarthome", "both"])
    p_pub.add_argument("--scenario", default="normal",
                       choices=["normal", "heatwave", "fire_alert", "night"])
    p_pub.add_argument("--interval", type=int, default=5)

    # listen
    sub.add_parser("listen", help="Subscribe and write all data to InfluxDB")

    # init
    sub.add_parser("init", help="Create default iotlab_config.json")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args.config)

    elif args.command == "read":
        cmd_read(args.measurement, args.hours, args.config)

    elif args.command == "stats":
        cmd_stats(args.measurement, args.hours, args.config)

    elif args.command == "export":
        cmd_export(args.measurement, args.hours,
                   args.output, args.config)

    elif args.command == "publish":
        cmd_publish(args.mode, args.scenario,
                    args.interval, args.config)

    elif args.command == "listen":
        cmd_listen(args.config)

    elif args.command == "init":
        import json, shutil
        from pathlib import Path
        src = Path(__file__).parent.parent / "iotlab_config.json"
        dst = Path("iotlab_config.json")
        if dst.exists():
            print(f"iotlab_config.json already exists.")
        else:
            shutil.copy(src, dst)
            print(f"✓  Created iotlab_config.json — edit it with your credentials.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
