/*
  ============================================================
  ESZG517 — Internet of Things: Design and Development
  Lab Session L1 — Sensor to Cloud
  Student Skeleton File: l1_arduino.ino
  Platform: ESP32 DevKit V1

  Name   : ___________________________
  USN    : ___________________________
  Date   : ___________________________

  Instructions:
    - Read every comment before writing any code.
    - Complete every section marked with TODO.
    - Do NOT delete any existing comments or includes.
    - Use the Serial Monitor (115200 baud) to debug your output.
    - Ask the instructor if you are stuck for more than 10 minutes.

  What this sketch does when complete:
    Reads temperature, humidity, pressure, CO2, and AQI from sensors
    connected to the ESP32, formats the data as JSON, and publishes
    it to HiveMQ Cloud via MQTT over TLS (port 8883).
    This is the hardware implementation of the same pipeline
    that l1_publisher.py implements in software.

  Hardware connections:
    DHT22 DATA pin  --> GPIO 15
    DHT22 VCC       --> 3.3V
    DHT22 GND       --> GND
    BMP280 SDA      --> GPIO 21
    BMP280 SCL      --> GPIO 22
    BMP280 VCC      --> 3.3V
    BMP280 GND      --> GND
    MQ135 AOUT      --> GPIO 34 (analogue input)
    MQ135 VCC       --> 5V
    MQ135 GND       --> GND

  Libraries required (install via Arduino Library Manager):
    - DHT sensor library by Adafruit
    - Adafruit BMP280 Library
    - PubSubClient by Nick O'Leary
    - ArduinoJson by Benoit Blanchon
    - WiFiClientSecure (built into ESP32 Arduino core)
  ============================================================
*/


// ============================================================
// SECTION 1 — INCLUDES
// These libraries are already included for you.
// You do not need to change anything here.
// ============================================================

#include <WiFi.h>               // ESP32 Wi-Fi library
#include <WiFiClientSecure.h>   // TLS-capable TCP client
#include <PubSubClient.h>       // MQTT client library
#include <DHT.h>                // DHT22 temperature and humidity sensor
#include <Adafruit_BMP280.h>    // BMP280 pressure sensor
#include <ArduinoJson.h>        // JSON serialisation library
#include <time.h>               // NTP time synchronisation


// ============================================================
// SECTION 2 — CONFIGURATION
// Fill in your personal details and credentials below.
// ============================================================

// TODO 2.1 — Replace with your Wi-Fi network name and password
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// TODO 2.2 — Replace with your HiveMQ Cloud cluster URL
// It looks like: xxxxxxxx.s1.eu.hivemq.cloud
const char* BROKER   = "YOUR_CLUSTER_URL_HERE";

// TODO 2.3 — Port for TLS connections. HiveMQ Cloud requires 8883.
const int   PORT     = 0;  // TODO: set the correct TLS port

// TODO 2.4 — Replace with your HiveMQ credentials
const char* MQTT_USER = "YOUR_USERNAME_HERE";
const char* MQTT_PASS = "YOUR_PASSWORD_HERE";

// TODO 2.5 — Replace YOURUSN with your actual university student number
// Your USN must appear here so the instructor can identify your data
const char* DEVICE_ID = "YOURUSN";

// TODO 2.6 — Construct the MQTT topic using your DEVICE_ID
// The topic structure is: eszg517/lab/weather/<your_USN>
// In C++ you cannot concatenate const char* with +
// Use the String class: String topic = "eszg517/lab/weather/" + String(DEVICE_ID);
// Then convert to const char* when publishing: topic.c_str()
String TOPIC = "eszg517/lab/weather/" + String(DEVICE_ID);

// Publish interval in milliseconds (5000 = 5 seconds)
const long PUBLISH_INTERVAL = 5000;

// DHT22 sensor pin
#define DHTPIN  15
#define DHTTYPE DHT22


// ============================================================
// SECTION 3 — GLOBAL OBJECTS
// These are created once and used throughout the sketch.
// You do not need to change anything here.
// ============================================================

WiFiClientSecure  tlsClient;    // TLS-capable TCP client
PubSubClient      mqttClient(tlsClient);  // MQTT client using TLS
DHT               dht(DHTPIN, DHTTYPE);  // DHT22 sensor object
Adafruit_BMP280   bmp;                   // BMP280 sensor object

// Timer variable for non-blocking publish interval
unsigned long lastPublishTime = 0;


// ============================================================
// SECTION 4 — Wi-Fi CONNECTION
// ============================================================

void connectWiFi() {
    Serial.print("[WiFi] Connecting to ");
    Serial.print(WIFI_SSID);

    // TODO 4.1 — Start the Wi-Fi connection.
    // Use WiFi.begin(WIFI_SSID, WIFI_PASSWORD) to initiate the connection.


    // TODO 4.2 — Wait until connected.
    // Use a while loop: while (WiFi.status() != WL_CONNECTED)
    // Inside the loop: delay(500) and Serial.print(".")
    // This blocks until the ESP32 gets an IP address.


    // Print success message — you do not need to change this
    Serial.println();
    Serial.print("[WiFi] Connected. IP address: ");
    Serial.println(WiFi.localIP());
}


// ============================================================
// SECTION 5 — MQTT CONNECTION AND CALLBACK
// ============================================================

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    /*
      This callback fires when a subscribed message arrives.
      In this session we are only publishing, not subscribing,
      so this function body can remain empty.
      It will be used in later sessions.
    */
}

void connectMQTT() {
    /*
      Connects to the HiveMQ Cloud MQTT broker.
      Retries every 5 seconds until successful.
      HiveMQ Cloud requires TLS — unencrypted connections are rejected.
    */

    // TODO 5.1 — Configure TLS.
    // HiveMQ Cloud uses a certificate signed by a trusted CA.
    // For development we can skip certificate verification using:
    // tlsClient.setInsecure();
    // Note: In production systems you should provide the root CA certificate.
    // Think about: what is the security implication of setInsecure()?


    // TODO 5.2 — Set the broker address and port on the MQTT client.
    // Use mqttClient.setServer(BROKER, PORT)


    // TODO 5.3 — Register the message callback.
    // Use mqttClient.setCallback(onMqttMessage)


    // Retry loop — keep trying until connected
    while (!mqttClient.connected()) {
        Serial.print("[MQTT] Connecting as ");
        Serial.print(DEVICE_ID);
        Serial.print("...");

        // TODO 5.4 — Attempt to connect to the broker.
        // Use mqttClient.connect(DEVICE_ID, MQTT_USER, MQTT_PASS)
        // This returns true on success, false on failure.
        // If successful: print "[MQTT] Connected" and the topic name
        // If failed: print the error state using mqttClient.state()
        //            then delay(5000) before retrying

        // Write your if/else here:

    }
}


// ============================================================
// SECTION 6 — SENSOR READING
// ============================================================

void readSensors(float &temperature, float &humidity,
                 float &pressure, float &co2_ppm, float &aqi) {
    /*
      Reads values from the DHT22 and BMP280 sensors.
      The MQ135 requires a warm-up period and calibration curve
      that is beyond this session's scope, so AQI and CO2 are
      simulated with a realistic random value.

      Parameters are passed by reference (&) so the function
      can write values back to the calling code.

      After reading, check for NaN (Not a Number):
        if (isnan(temperature)) — the sensor read failed
    */

    // TODO 6.1 — Read temperature from the DHT22 sensor.
    // Use dht.readTemperature() — returns a float in Celsius.
    // If the reading is NaN, print a warning and set a default value of 0.0
    temperature = 0.0;  // replace this


    // TODO 6.2 — Read humidity from the DHT22 sensor.
    // Use dht.readHumidity() — returns a float as a percentage.
    // Same NaN check as above.
    humidity = 0.0;  // replace this


    // TODO 6.3 — Read pressure from the BMP280 sensor.
    // Use bmp.readPressure() — returns pressure in Pascals.
    // Convert to hPa by dividing by 100.0
    // Example: pressure = bmp.readPressure() / 100.0;
    pressure = 0.0;  // replace this


    // TODO 6.4 — Simulate CO2 and AQI readings.
    // The MQ135 requires complex calibration beyond this session.
    // Simulate realistic values:
    //   CO2  : random value between 400 and 600 ppm
    //   AQI  : random value between 20 and 80
    // Use: random(low, high) which returns a long integer
    //      cast to float: (float)random(400, 600)
    co2_ppm = 0.0;  // replace this
    aqi     = 0.0;  // replace this
}


// ============================================================
// SECTION 7 — PAYLOAD CONSTRUCTION AND PUBLISH
// ============================================================

void publishReading() {
    /*
      Reads sensor values, constructs a JSON payload,
      and publishes it to the MQTT broker.

      JSON format must match the payload specification in the brief:
      {
        "device_id"  : "YOURUSN",
        "temperature": 26.40,
        "humidity"   : 62.10,
        "pressure"   : 1013.20,
        "co2_ppm"    : 412.00,
        "aqi"        : 52.00,
        "timestamp"  : 1713441600
      }
    */

    // Read sensor values into local variables
    float temperature, humidity, pressure, co2_ppm, aqi;
    readSensors(temperature, humidity, pressure, co2_ppm, aqi);

    // TODO 7.1 — Create a JSON document.
    // ArduinoJson uses a StaticJsonDocument to serialise data.
    // The number in angle brackets is the buffer size in bytes.
    // 256 bytes is sufficient for this payload.
    // Example: StaticJsonDocument<256> doc;
    StaticJsonDocument<256> doc;

    // TODO 7.2 — Add each field to the JSON document.
    // Use doc["field_name"] = value;
    // Example: doc["device_id"] = DEVICE_ID;
    // Add all 7 fields: device_id, temperature, humidity,
    //                   pressure, co2_ppm, aqi, timestamp
    // For timestamp: use time(nullptr) to get Unix epoch time


    // TODO 7.3 — Serialise the JSON document to a character buffer.
    // Use: char payload[256];
    //      serializeJson(doc, payload);
    // This converts the JSON document to a string that can be published.


    // TODO 7.4 — Publish the payload to the MQTT broker.
    // Use: mqttClient.publish(TOPIC.c_str(), payload)
    // The .c_str() converts the Arduino String to a const char*
    // This publishes at QoS 0 — PubSubClient uses QoS 0 by default.
    // Think about: how does this differ from the Python publisher's QoS 1?


    // TODO 7.5 — Print the payload to the Serial Monitor for debugging.
    // Format: [HH:MM:SS] PUB --> topic : payload
    Serial.print("[PUB] --> ");
    Serial.print(TOPIC);
    Serial.print(" : ");
    // Print your payload string here
}


// ============================================================
// SECTION 8 — SETUP
// Runs once when the ESP32 powers on or resets.
// ============================================================

void setup() {
    // Start Serial Monitor at 115200 baud
    Serial.begin(115200);
    delay(1000);

    Serial.println("================================================");
    Serial.println("  ESZG517 IoT Lab — L1 Publisher (ESP32)");
    Serial.print("  Device ID : "); Serial.println(DEVICE_ID);
    Serial.print("  Topic     : "); Serial.println(TOPIC);
    Serial.println("================================================");

    // TODO 8.1 — Initialise the DHT22 sensor.
    // Use dht.begin();


    // TODO 8.2 — Initialise the BMP280 sensor.
    // Use bmp.begin(0x76) — 0x76 is the default I2C address.
    // If begin() returns false, print an error message.
    // The I2C address may be 0x77 on some modules — try both if it fails.


    // TODO 8.3 — Connect to Wi-Fi.
    // Call your connectWiFi() function.


    // TODO 8.4 — Synchronise time using NTP.
    // The ESP32 needs accurate time for the timestamp field.
    // Use: configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    // Then wait until time is valid:
    // while (time(nullptr) < 1000000000) { delay(500); }
    // Think about: why does an IoT device need accurate time?


    // TODO 8.5 — Connect to the MQTT broker.
    // Call your connectMQTT() function.


    Serial.println("[SETUP] Ready. Publishing every 5 seconds.");
}


// ============================================================
// SECTION 9 — LOOP
// Runs continuously after setup() completes.
// ============================================================

void loop() {
    /*
      The loop() function runs as fast as the processor allows.
      We use a non-blocking timer (millis) to publish at intervals
      rather than delay(), which would freeze the MQTT keep-alive.
    */

    // TODO 9.1 — Reconnect if the MQTT connection was lost.
    // Check: if (!mqttClient.connected()) then call connectMQTT()
    // This handles network drops gracefully.


    // TODO 9.2 — Call mqttClient.loop() on every iteration.
    // This processes incoming messages and sends keep-alive PINGs.
    // Without this call the broker will disconnect the client.


    // TODO 9.3 — Publish a reading every PUBLISH_INTERVAL milliseconds.
    // Use millis() to track elapsed time non-blocking:
    //
    // unsigned long now = millis();
    // if (now - lastPublishTime >= PUBLISH_INTERVAL) {
    //     lastPublishTime = now;
    //     publishReading();
    // }
    //
    // Think about: why do we use millis() instead of delay(5000)?

}
