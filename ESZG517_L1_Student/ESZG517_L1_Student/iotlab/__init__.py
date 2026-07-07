"""
IoTLab Framework — ESZG517 IoT Virtual Lab
BITS Pilani · Work Integrated Learning Programmes

Usage:
    from iotlab import WeatherStation, SmartHome, IoTLabClient

Quickstart:
    client  = IoTLabClient()                   # reads iotlab_config.json
    weather = WeatherStation(client)
    weather.send(temperature=26.4, humidity=62.1, pressure=1013.2)
"""

from .config    import IoTLabConfig
from .sensor    import WeatherStation, SmartHome, SensorReading
from .mqtt_client import IoTLabMQTTClient
from .db_writer import IoTLabWriter
from .db_reader import IoTLabReader
from .client    import IoTLabClient

__version__  = "1.0.0"
__author__   = "ESZG517 IoT Virtual Lab"
__all__ = [
    "IoTLabConfig",
    "IoTLabClient",
    "IoTLabMQTTClient",
    "IoTLabWriter",
    "IoTLabReader",
    "WeatherStation",
    "SmartHome",
    "SensorReading",
]
