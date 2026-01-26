#include <Arduino.h>

#define FC_Serial Serial1  // UART0 on Pico 

const int rcInPin = 2; // GP2
const uint32_t FAILSAFE_MS = 500;

volatile uint16_t raw_throttle = 1000;
volatile uint16_t raw_yaw = 1500;
volatile uint32_t last_pulse_time = 0;
volatile uint32_t last_edge = 0;
volatile uint8_t channel_idx = 0;

// the "ear" basically...measures pulses in microseconds
void i_ppm_handler()
{
  uint32_t now = micros();
  uint32_t diff = now - last_edge;
  last_edge = now;

  if (diff > 3000)
  {
    channel_idx = 0;
    last_pulse_time = millis();
  }
  else
  {
    // we only care about specific channels 
    // standard ppm order is 1 roll, 2 pitch, 3 throtlle, 4 yaw
    if (channel_idx == 2) raw_throttle = diff;
    if (channel_idx == 3) raw_yaw = diff;
    channel_idx++;
  }
}

void setup()
{
  FC_Serial.setTX(0);
  FC_Serial.setRX(1);
  FC_Serial.begin(115200); // f405 expects this rate for msp

  pinMode(rcInPin, INPUT);
  attachInterrupt(digitalPinToInterrupt(rcInPin), i_ppm_handler, RISING);
}

void loop()
{
  uint32_t now = millis();

  // prepare the msp frame of 11 bytes
  uint8_t frame[12];
  frame[0] = 0x24;  // $
  frame[1] = 0x4d;  // M
  frame[2] = 0x3c;  // <

  uint16_t send_throttle, send_yaw;

  // failsafe logic
  if (now - last_pulse_time > FAILSAFE_MS)
  {
    send_throttle = 1000;  // kill motors
    send_yaw = 1500;   // stop spinning
  }
  else
  {
    send_throttle = raw_throttle;
    send_yaw = raw_yaw;
  }

  // packing 4 channels into 8 bytes
  // channels: roll (fixed), pitch (fixed), throttle (active), yaw (active)
  uint16_t channels_to_send[4] = {1500, 1500, send_throttle, send_yaw};

  int f_idx = 3;
  for (int i = 0; i < 4; i++)
  {
    uint16_t v = channels_to_send[i];
    if (v < 1000) v = 1000;
    if (v > 2000) v = 2000;
    frame[f_idx++] = (v >> 8) & 0xFF;  // high byte
    frame[f_idx++] = v & 0xFF;        // low byte
  }

  // checksum
  uint8_t checksum = 0;
  for (int i = 0; i < 11; i++) checksum ^= frame[i];
  frame[11] = checksum;

  // send to f405
  static uint32_t lastTx = 0;
  if (now - lastTx > 20) // 50 Hz update rate
  {
    FC_Serial.write(frame, 12);
    lastTx = now;
  }
}