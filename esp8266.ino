#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "TECNO CAMON 12 Air";
const char* password = "afms83/406";
const char* serverUrl = "https://pay-keyboard.onrender.com/tokens";

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print("......");
    }
    Serial.println("\nConnected to WiFi");
}

void loop() {
    if (WiFi.status() == WL_CONNECTED) {
        WiFiClient client;
        HTTPClient http;

        http.begin(client, serverUrl);
        int httpCode = http.GET();

        if (httpCode == 200) {
            String payload = http.getString();
            Serial.println("Tokens: " + payload);
        } else {
            Serial.println("Failed to fetch tokens");
        }

        http.end();
    }
    delay(60000);  // Fetch every 60 seconds
}
