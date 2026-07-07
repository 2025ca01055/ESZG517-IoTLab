/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  ESZG517 — IoT Systems and Applications                         ║
 * ║  Lab Session L2 — Storage, Query & Visualisation                ║
 * ║  File : l2_arduino.ino            (Student Version)             ║
 * ╚══════════════════════════════════════════════════════════════════╝
 *
 * HOW THIS FILE WORKS
 * ───────────────────
 *   Each function has a box showing the exact code to type.
 *   Read the box → type it into the blank below.
 *
 * LIBRARIES  (Arduino IDE → Tools → Manage Libraries)
 *   PubSubClient  by Nick O'Leary
 *   ArduinoJson   by Benoit Blanchon
 *
 * BOARD: ESP32 Dev Module | Monitor Speed: 115200
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ── Credentials — fill these in ───────────────────────────────────────────────
const char* WIFI_SSID       = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD   = "YOUR_WIFI_PASSWORD";
const char* MQTT_HOST       = "YOUR_HIVEMQ_HOST";
const int   MQTT_PORT       = 8883;
const char* MQTT_USER       = "YOUR_HIVEMQ_USERNAME";
const char* MQTT_PASS       = "YOUR_HIVEMQ_PASSWORD";
const char* DEVICE_ID       = "YOUR_STUDENT_ID";
const char* SUBSCRIBE_TOPIC = "eszg517/lab/weather/+";

WiFiClientSecure wifiClient;
PubSubClient     mqttClient(wifiClient);

// ══════════════════════════════════════════════════════════════════════════════
// connectWiFi — already complete, do not change
// ══════════════════════════════════════════════════════════════════════════════

void connectWiFi() {
  Serial.print("[WiFi] Connecting to "); Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500); Serial.print("."); attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP: "); Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Failed — check SSID and password.");
  }
}


// ══════════════════════════════════════════════════════════════════════════════
// FUNCTION 1 — onMqttMessage
// ══════════════════════════════════════════════════════════════════════════════

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  /*
   * ╔══ ANSWER — DEMO sensors 1–5 (type into blank below) ════════════════╗
   *                                                                         *
   *   String jsonStr = "";                                                  *
   *   for (int i = 0; i < length; i++) jsonStr += (char)payload[i];        *
   *                                                                         *
   *   StaticJsonDocument<512> doc;                                          *
   *   DeserializationError err = deserializeJson(doc, jsonStr);            *
   *   if (err) { Serial.println("[ERROR] JSON failed"); return; }          *
   *                                                                         *
   *   const char* deviceId  = doc["device_id"]  | "unknown";              *
   *   float temperature     = doc["temperature"] | 0.0f;                   *
   *   float humidity        = doc["humidity"]    | 0.0f;                   *
   *   float pressure        = doc["pressure"]    | 0.0f;                   *
   *   float co2             = doc["co2_ppm"]     | 0.0f;                   *
   *   float aqi             = doc["aqi"]         | 0.0f;                   *
   *                                                                         *
   *   Serial.println("──────────────────────────────────────");            *
   *   Serial.print("[MSG] Device    : "); Serial.println(deviceId);        *
   *   Serial.print("      Temp      : "); Serial.print(temperature);       *
   *                                       Serial.println(" C");            *
   *   Serial.print("      Humidity  : "); Serial.print(humidity);          *
   *                                       Serial.println(" %");            *
   *   Serial.print("      Pressure  : "); Serial.print(pressure);          *
   *                                       Serial.println(" hPa");          *
   *   Serial.print("      CO2       : "); Serial.print(co2);               *
   *                                       Serial.println(" ppm");          *
   *   Serial.print("      AQI       : "); Serial.println(aqi);             *
   *   Serial.println("──────────────────────────────────────");            *
   *                                                                         *
   * ╠══ ANSWER — YOUR ASSIGNMENT: add sensors 6–10 ═══════════════════════╣
   *                                                                         *
   *   After the demo sensor declarations, add:                             *
   *   float lightLevel    = doc["light_level"]     | 0.0f;                 *
   *   float windSpeed     = doc["wind_speed"]       | 0.0f;                *
   *   float rainfall      = doc["rainfall"]         | 0.0f;                *
   *   float batteryVolt   = doc["battery_voltage"]  | 0.0f;                *
   *   int   rssi          = doc["rssi"]             | 0;                   *
   *                                                                         *
   *   Then print each one the same way as the demo sensors above.          *
   *                                                                         *
   * ╚═════════════════════════════════════════════════════════════════════╝
   */

  // ── TYPE YOUR CODE HERE ─────────────────────────────────────────────────────



  // ── END ─────────────────────────────────────────────────────────────────────
}


// ══════════════════════════════════════════════════════════════════════════════
// FUNCTION 2 — connectMQTT
// ══════════════════════════════════════════════════════════════════════════════

void connectMQTT() {
  /*
   * ╔══ ANSWER — type the lines below into the blank ══════════════════════╗
   *                                                                         *
   *   wifiClient.setInsecure();                                             *
   *   mqttClient.setServer(MQTT_HOST, MQTT_PORT);                          *
   *   mqttClient.setCallback(onMqttMessage);                               *
   *                                                                         *
   *   String clientId = "ESP32_" + String(DEVICE_ID);                     *
   *   if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS)) {   *
   *       Serial.println("[MQTT] Connected!");                             *
   *       mqttClient.subscribe(SUBSCRIBE_TOPIC, 1);                        *
   *       Serial.print("[MQTT] Subscribed to: ");                          *
   *       Serial.println(SUBSCRIBE_TOPIC);                                 *
   *   } else {                                                              *
   *       Serial.print("[MQTT] Failed, state=");                           *
   *       Serial.println(mqttClient.state());                              *
   *   }                                                                     *
   *                                                                         *
   * ╚═════════════════════════════════════════════════════════════════════╝
   */

  // ── TYPE YOUR CODE HERE ─────────────────────────────────────────────────────



  // ── END ─────────────────────────────────────────────────────────────────────
}


// ══════════════════════════════════════════════════════════════════════════════
// setup — already complete, do not change
// ══════════════════════════════════════════════════════════════════════════════

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("================================================");
  Serial.println("  ESZG517 IoT Lab — L2 Arduino Subscriber");
  Serial.print  ("  Device   : "); Serial.println(DEVICE_ID);
  Serial.print  ("  Topic    : "); Serial.println(SUBSCRIBE_TOPIC);
  Serial.println("================================================");
  connectWiFi();
  connectMQTT();
}


// ══════════════════════════════════════════════════════════════════════════════
// FUNCTION 3 — loop
// ══════════════════════════════════════════════════════════════════════════════

void loop() {
  /*
   * ╔══ ANSWER — type the lines below into the blank ══════════════════════╗
   *                                                                         *
   *   if (!mqttClient.connected()) {                                        *
   *       Serial.println("[MQTT] Reconnecting...");                        *
   *       while (!mqttClient.connected()) {                                *
   *           connectMQTT();                                               *
   *           if (!mqttClient.connected()) delay(5000);                    *
   *       }                                                                 *
   *   }                                                                     *
   *   mqttClient.loop();                                                   *
   *                                                                         *
   * ╚═════════════════════════════════════════════════════════════════════╝
   */

  // ── TYPE YOUR CODE HERE ─────────────────────────────────────────────────────



  // ── END ─────────────────────────────────────────────────────────────────────
}
