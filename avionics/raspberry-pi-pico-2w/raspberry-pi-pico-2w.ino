#include <TinyGPS++.h>
#include <Servo.h>
#include <WiFi.h>

WiFiClient client;
Servo myServo;
TinyGPSPlus gps;

const char* ssid = "sejong-guest";
const char* password = "0234083114";
const char* host = "172.19.20.99";
const uint16_t port = 3002; 

const int ledPin = LED_BUILTIN;

int servoPin = 16;
unsigned long lastMoveTime = 0;
int servoStage = 0;

void setup() 
{
  Serial.begin(115200);
  Serial1.begin(9600);
  pinMode(ledPin, OUTPUT);
  myServo.attach(servoPin);

  // connect to wifi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");
}

void loop() 
{
  unsigned long currentMillis = millis();

  if (!client.connected())
  {
    client.connect(host, port);
  }

  // non blocking servo logic
  if (currentMillis - lastMoveTime >= 1000) 
  {
    lastMoveTime = currentMillis;
    if (servoStage == 0) { myServo.write(0);   digitalWrite(ledPin, HIGH); servoStage = 1; }
    else if (servoStage == 1) { myServo.write(90);  digitalWrite(ledPin, LOW);  servoStage = 2; }
    else { myServo.write(180); digitalWrite(ledPin, HIGH); servoStage = 0; }
  }

  // gps 
  while (Serial1.available() > 0) 
  {
    if (gps.encode(Serial1.read())) 
    {
      if (gps.location.isUpdated() && gps.location.isValid()) 
      {
        String gpsData = "GPS," + String(gps.location.lat(), 6) + "," + 
                          String(gps.location.lng(), 6) + "," +
                          String(gps.altitude.meters());
        
        if (client.available())
        {
          client.println(gpsData);
        }
        Serial.println("Sent: " + gpsData);
      }
    }
  }
}