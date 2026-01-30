#include <TinyGPS++.h>
#include <Servo.h>

Servo myServo;
TinyGPSPlus gps;

int servoPin = 16;

void setup()
{
  Serial.begin(115200);
  Serial1.begin(9600);

  while(!Serial);

  myServo.attach(servoPin);
}

void loop()
{
  // Sweep from 0 to 180 degrees
  myServo.write(0);
  delay(1000);
  myServo.write(90);
  delay(1000);
  myServo.write(180);
  delay(1000);
  
  // see serial output for lat, lon and alt
  if (Serial1.available())
  {
    if (gps.encode(Serial1.read()))
    {
      if (gps.location.isValid())
      {
        Serial.print("Lat: "); Serial.println(gps.location.lat(), 6);
        Serial.print("Lon: "); Serial.println(gps.location.lng(), 6);
        Serial.print("Alt: "); Serial.println(gps.altitude.meters());
      }
    }
  }
}