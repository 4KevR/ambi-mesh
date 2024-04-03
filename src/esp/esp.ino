#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>
#include <EEPROM.h>
#include <ESP8266WebServer.h>
#include <ESP8266WiFi.h>
#include <UUID.h>
#include <WiFiUdp.h>

/* Global definitions */

#define NEO_PIXEL_PIN 3
#define SSID_LENGTH 32
#define PASSWORD_LENGTH 64

struct SavedData {
  char uuid[64];
  char ssid[SSID_LENGTH];
  char password[PASSWORD_LENGTH];
  int numPixels;
};
SavedData savedData;

ESP8266WebServer server(80);
DynamicJsonDocument doc(4096);

WiFiUDP Multicast;
IPAddress multicastIP(239, 100, 101, 102);
constexpr uint16_t multicastPort = 6000;
char multicastBuffer[255];

WiFiServer tcpServer(6001);
WiFiClient client;
unsigned long lastTcpData;
bool gotFirstLedData;

bool reserved = false;
bool isConfigured = false;
IPAddress reservedBy;

Adafruit_NeoPixel pixels = Adafruit_NeoPixel(0, NEO_PIXEL_PIN, NEO_GRB + NEO_KHZ800);

/* EEPROM management */

void loadSavedData() {
  EEPROM.get(0, savedData);
  if (savedData.numPixels > 0) {
    isConfigured = true;
  }
}

void saveSavedData() {
  EEPROM.put(0, savedData);
  EEPROM.commit();
}

void resetConfig() {
  for (int i = 0; i < sizeof(SavedData); i++) {
    EEPROM.write(i, 0);
  }
  EEPROM.end();
}

/* Configuration WiFi AP Setup */

void setupWiFiStation() {
  const char* ssid = "Ambient Light Station";
  const char* password = "config1234";
  WiFi.softAP(ssid, password);
  Serial.println("Please connect to the 'Ambient Light Station' network and proceed with the configuration...");
}

/* HTTP Server Handlers */

void handle_getConfigure() {
  String html = "<!DOCTYPE HTML>\r\n";
  html += "<html>\r\n";
  html += "<body>\r\n";
  html += "<h1>Ambi mesh node</h1>\r\n";
  html += "<form method='post' action='/configure'>\r\n";
  html += "SSID: <input type='text' name='ssid'><br>\r\n";
  html += "Password: <input type='password' name='password'><br>\r\n";
  html += "Amount of NeoPixel LEDs: <input type='text' name='numPixels'><br>\r\n";
  html += "<input type='submit' value='Submit'>\r\n";
  html += "</form></body>\r\n";
  html += "</html>\r\n";
  server.send(200, "text/html", html);
}

String handle_postConfigure() {
  if (server.args() == 3) {
    String ssid = server.arg("ssid");
    String password = server.arg("password");
    int numPixels = server.arg("numPixels").toInt();

    if (numPixels <= 0) {
      return "Invalid amount of NeoPixel leds";
    }

    UUID uuid;
    uint32_t seed1 = random(999999999);
    uint32_t seed2 = random(999999999);
    uuid.seed(seed1, seed2);
    uuid.generate();
    strncpy(savedData.uuid, uuid.toCharArray(), 64);
    strncpy(savedData.ssid, ssid.c_str(), SSID_LENGTH);
    strncpy(savedData.password, password.c_str(), PASSWORD_LENGTH);
    savedData.numPixels = numPixels;

    saveSavedData();

    isConfigured = true;
    ESP.restart();

    return "Configuration saved. Restarting...";
  }
  return "Invalid number of arguments";
}

void handle_getHome() {
  String html = "<!DOCTYPE HTML>\r\n";
  html += "<html>\r\n";
  html += "<body>\r\n";
  html += "<h1>Ambi mesh node</h1>\r\n";
  html += "<p>This is mesh node with uuid ";
  html += savedData.uuid;
  html += "</p>\r\n";
  html += "<form method='post' action='/reset'>\r\n";
  html += "<input type='submit' value='Reset'>\r\n";
  html += "</form></body>\r\n";
  html += "</html>\r\n";
  server.send(200, "text/html", html);
}

String handle_postReset() {
  resetConfig();
  ESP.restart();
  return "Reset completed";
}

void handle_NotFound() {
  server.send(404, "text/plain", "Not found");
}

/* TCP & UDP Servers */

void handle_multicastServer() {
  uint16_t packetSize = Multicast.parsePacket();
  if (packetSize) {
    Multicast.read(multicastBuffer, sizeof(multicastBuffer));
    multicastBuffer[packetSize] = 0;
    if (strstr(multicastBuffer, "reconnaissance")) {
      Serial.print("Received reconnaissance from ");
      Serial.println(Multicast.remoteIP());
      Multicast.beginPacket(Multicast.remoteIP(), multicastPort);
      DynamicJsonDocument doc(1024);
      doc["uuid"] = savedData.uuid;
      doc["reserved"] = reserved;
      doc["amount_of_leds"] = savedData.numPixels;
      String jsonData;
      serializeJson(doc, jsonData);
      Multicast.print(jsonData);
      Multicast.endPacket();
    }
  }
}

void handle_tcpServer() {
  if (client) {
    String data = "";
    if (client.connected() && client.available()) {
      bool lastTerminating = false;
      while (!lastTerminating) {
        int inByte = client.read();
        if (inByte >= 0) {
          char c = (char)inByte;
          if (c == '\n') {
            if (reserved) {
              if (data.equals("selecting")) {
                Serial.println("Client is selecting range");
                client.write("ack");
                apply_neoPixel(200);
              } else if (data.equals("ready")) {
                Serial.println("Client is ready to transmit");
                client.write("ack");
                apply_neoPixel(0);
              } else if (data.equals("disconnect")) {
                if (reserved && reservedBy.toString().equals(client.remoteIP().toString())) {
                  Serial.println("Client sent request to disconnect");
                  client.write("ack");
                  reserved = false;
                  reservedBy = IPAddress();
                  apply_neoPixel(0);
                  client.stop();
                }
              } else {
                gotFirstLedData = true;
                lastTcpData = millis();
                handle_hexArray(data);
                client.write("ack");
              }
            } else {
              if (data.equals("reserve")) {
                Serial.println("Client reserved connection");
                client.write("ack");
                reserved = true;
                reservedBy = client.remoteIP();
              }
            }
            data = "";
            lastTerminating = true;
          } else {
            data += c;
          }
        }
      }
    }
  } else {
    client = tcpServer.available();
    if (client) {
      Serial.print("Got TCP connection from ");
      Serial.println(client.remoteIP());
      lastTcpData = millis();
      gotFirstLedData = false;
    }
  }
  if (reserved && millis() - lastTcpData > 15000 + int(!gotFirstLedData) * 105000) {
    Serial.println("Client timeout reached, closing connection");
    reserved = false;
    reservedBy = IPAddress();
    apply_neoPixel(0);
    client.stop();
  }
}

/* NeoPixel management */

void handle_hexArray(const String& hex_array) {
  for (int i = 0; i < savedData.numPixels; i++) {
    long int colorHex = strtol(hex_array.substring(i * 6, (1 + i) * 6).c_str(), NULL, 16);
    int r = (colorHex >> 16) & 0xFF;
    int g = (colorHex >> 8) & 0xFF;
    int b = colorHex & 0xFF;
    pixels.setPixelColor(i, pixels.Color(r, g, b));
  }
  pixels.show();
}

void apply_neoPixel(int num) {
  for (int i = 0; i < savedData.numPixels; i++) {
    pixels.setPixelColor(i, pixels.Color(num, num, num));
  }
  pixels.show();
}

/* Setup */

void setup() {
  EEPROM.begin(sizeof(SavedData));

  Serial.begin(115200);
  delay(100);

  Serial.println("Hello from ambi-mesh node");

  loadSavedData();

  if (!isConfigured) {
    Serial.println("No configuration found, entering AP mode");
    setupWiFiStation();
    server.on("/", HTTP_GET, handle_getConfigure);
    server.on("/configure", HTTP_POST, handle_postConfigure);
    server.onNotFound(handle_NotFound);
    server.begin();
    Serial.println("HTTP server started");
  } else {
    Serial.print("Configuration loaded, trying to connect");
    WiFi.begin(savedData.ssid, savedData.password);
    int connectionCounter = 0;
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
      connectionCounter += 1;
      if (connectionCounter >= 20) {
        resetConfig();
        Serial.println("\nConfig incorrect, resetting device");
        ESP.restart();
      }
    }

    Serial.println("");
    Serial.println("WiFi connected!");
    Serial.print("Got IP: ");
    Serial.println(WiFi.localIP());

    server.on("/", HTTP_GET, handle_getHome);
    server.on("/reset", HTTP_POST, handle_postReset);
    server.onNotFound(handle_NotFound);
    server.begin();

    pixels.updateLength(savedData.numPixels);
    pixels.begin();
    Multicast.beginMulticast(WiFi.localIP(), multicastIP, multicastPort);
    tcpServer.begin();

    apply_neoPixel(0);
    delay(500);
    apply_neoPixel(200);
    delay(500);
    apply_neoPixel(0);
    Serial.println("Setup completed, ready to accept connections");
  }
}

/* Main loop */

void loop() {
  server.handleClient();
  handle_multicastServer();
  handle_tcpServer();
}