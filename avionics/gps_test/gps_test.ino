#include <TinyGPS++.h>

TinyGPSPlus gps;

void setup()
{
  Serial.begin(115200);
  Serial1.begin(9600);

  while(!Serial);
}

void loop()
{
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