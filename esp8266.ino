#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "TECNO CAMON 12 Air";
const char* password = "afms83/406";
const char* serverUrl = "https://pay-keyboard.onrender.com";  // Backend URL

String storedTokens[10];  // Store up to 10 tokens
int tokenCount = 0;

void setup() {
    Serial.begin(115200);
    WiFi.begin(ssid, password);
    Serial.println("Connecting to WiFi...");

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("\nConnected to WiFi");
    fetchTokens();  // Fetch tokens on startup
}

void loop() {
    if (Serial.available()) {
        String userToken = Serial.readStringUntil('\n');
        userToken.trim();
        
        if (isValidToken(userToken)) {
            Serial.println("✅ Token is valid! Activating relay...");
            digitalWrite(D1, HIGH);  // Simulating relay activation
            delay(5000);
            digitalWrite(D1, LOW);
        } else {
            Serial.println("❌ Invalid or used token.");
        }
    }
    
    delay(30000);  // Fetch new tokens every 30 seconds
    fetchTokens();
}

// Fetch Unused Tokens from Backend
void fetchTokens() {
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(serverUrl + String("/tokens"));
        int httpResponseCode = http.GET();

        if (httpResponseCode == 200) {
            String response = http.getString();
            Serial.println("Fetched Tokens: " + response);

            DynamicJsonDocument doc(512);
            deserializeJson(doc, response);

            tokenCount = doc["tokens"].size();
            for (int i = 0; i < tokenCount; i++) {
                storedTokens[i] = doc["tokens"][i].as<String>();
            }
        }
        
        http.end();
    }
}

// Check Token Validity
bool isValidToken(String token) {
    for (int i = 0; i < tokenCount; i++) {
        if (storedTokens[i] == token) {
            // Mark as used in backend
            HTTPClient http;
            http.begin(serverUrl + String("/verify-token"));
            http.addHeader("Content-Type", "application/json");

            String jsonPayload = "{\"token\":\"" + token + "\"}";
            int httpResponseCode = http.POST(jsonPayload);
            http.end();

            return httpResponseCode == 200;
        }
    }
    
    return false;
}
