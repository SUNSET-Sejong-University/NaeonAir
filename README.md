# NaeonAir — AI‑IoT Crowd Management Payload for UAVs
<p align="center">
  <img src="https://github.com/user-attachments/assets/3af632ba-ae9c-485a-a9d6-fc42f9d9f66b" width="280" alt="AIEyeInTheSky" />
</p>
Prototype project: an AI‑IoT payload designed to be mounted on small UAVs to assist with crowd monitoring and crowd‑management tasks. The device integrates a camera, GPS, microcontroller, flight controller interface, and a servo to provide real‑time observation and controlled interventions intended to reduce the risk of crowd-related accidents.

> Warning: This project is a research prototype. Use only in accordance with local laws and aviation regulations. Deploying airborne systems near crowds or public events carries safety, privacy, and legal responsibilities. The authors are not responsible for misuse.

## Project overview
NaeonAir is an add‑on payload that fits on a small UAV and performs real‑time crowd observation and simple crowd management actions. The prototype combines:
- a camera module (ESP‑CAM OV2640) for video capture/edge inference,
- a Raspberry Pi Pico W for coordinating IO and peripherals,
- a GPS (NEO‑6M) for location/time stamping and geofencing,
- an F405 V4 flight controller for UAV integration and power distribution,
- ESCs and a LiPo battery for power,
- a servo for mechanical actuation (e.g., pointing a marker, deploying a small visual/aural indicator).

This README documents the prototype wiring and provides guidance for getting started and testing.

## Motivation
A primary motivation is reducing risks during high-density events where mismanagement or panic can create dangerous crush conditions (for example, the Itaewon incident motivated safer crowd monitoring). The device is intended to provide:
- real‑time situational awareness,
- geolocated observations,
- a mechanism for simple, safe crowd‑level signaling from the air (non-contact),
- a research platform for developing detection and guidance algorithms.

## Key features
- Onboard camera for live streaming and on‑device inference experiments
- GPS tagging of images/video for spatial context
- Servo for controlled small actuations (visual cues / signaling)
- Integration with standard flight controllers for power and telemetry
- Modular wiring for easy replacement of components

## Circuit summary
Summary:
- Power is provided by the 3S Li‑Po battery via XT60 connectors and distributed by the ESCs and flight controller.
- The ESCs provide a 5V output used to power the F405 flight controller and the ESP‑CAM.
- The Raspberry Pi Pico 2W is used as the main payload microcontroller (communication with GPS and servo control).
- GPS NEO‑6M provides location; it connects to the Pico serial pins (RX/TX).
- ESP‑CAM receives 5V from ESC 5V out and ground from ESC GND out.
- The F405 flight controller handles power distribution to the servo (5V / GND) and provides telemetry and other interfaces for UAV control.

<p align="center">
  <img src="https://github.com/user-attachments/assets/3026fc20-5ac4-4f5c-87d6-9f42ac98cca2" width="420" alt="Circuit Design" />
</p>

### Wiring highlights:
- ESC Battery VCC → XT60 + → Li‑Po + terminal
- ESC Battery GND → XT60 - → Li‑Po - terminal
- ESC 5V out → F405 5V (Barometer pin as power source) and ESP‑CAM 5V
- ESC GND out → F405 GND and ESP‑CAM GND
- Raspberry Pi Pico:
  - VSYS → F405 5V (power feed)
  - 3V3_OUT → GPS VCC (3.3V)
  - GPIO0 → GPS RX
  - GPIO1 → GPS TX
  - GPIO16 → SERVO SIGNAL
  - GND → shared GND (GPS GND and F405 GND)
- GPS NEO‑6M: VCC (3.3V) → Pico 3V3_VREF; RX/TX ↔ Pico GPIO0/1; GND → shared GND
- ESP‑CAM OV2640: 5V → ESC 5V out; GND → ESC GND out
- F405 V4 Flight Controller:
  - 5V Pin → Servo POWER
  - GND Pin → Servo GND
  - SBUS / UART pins → (optional) receiver / telemetry

Note: This summary is derived from the provided circuit documentation — always verify voltages and wiring for your specific hardware revisions. Many versions of the ESP‑CAM prefer 5V on the 5V pin but expect 3.3V IO levels; check module datasheets.

<p align="center">
  <img src="https://github.com/user-attachments/assets/d8fbcdfc-298a-4e9d-81c1-8dfc6175d096" width="420" alt="Prototype device mounted on stand" />
</p>

## Mounting & mechanical notes
- Keep the camera unobstructed and leveled relative to the UAV body to simplify computer-vision calibration.
- Place the GPS module as high and away from noisy electronics when possible for better reception.
- Keep the Pico and ESP‑CAM away from high‑current traces to reduce noise; add decoupling capacitors where needed.
- Secure the payload with vibration‑damping mounts if possible — vibrations can degrade both GPS reliability and image quality.

## Software / firmware overview
This prototype uses three main software pieces:
1. Raspberry Pi Pico 2W firmware
   - Handles GPS serial, servo PWM control on GPIO16, and acts as a coordination node for sensor timestamps.
   - Suggested languages: MicroPython or C/C++ (SDK).
2. ESP‑CAM firmware
   - Provides camera capture and Wi‑Fi streaming; can run basic edge inference (e.g., a lightweight person‑detection model) if sufficient resources are available.
   - Typically flashed via Arduino IDE or ESP‑Toolchain.
3. Ground / backend software
   - Receives video/telemetry, logs GPS positions, and visualizes crowd density. Could be a simple Flask/Node server or a cloud service.

Suggested next steps for software:
- Implement a lightweight detection model (e.g., MobileNet SSD or a small YOLO variant) on a ground server or on‑device if compute allows.
- Add geofencing logic to prevent operation in restricted areas.
- Timestamp frames with GPS time for synchronized logging.

## Quick start — basic power & test sequence
1. Verify all wiring carefully while battery is disconnected.
2. Connect Li‑Po (ensure correct polarity).
3. Power up the system and confirm:
   - ESC 5V is present and powers the flight controller and ESP‑CAM.
   - Pico receives power and boots.
   - GPS acquires a fix (may require outdoor view of sky).
   - ESP‑CAM serves a stream (connect to its IP address) or blinks as expected.
4. Test servo:
   - Run a small test script on the Pico to sweep GPIO16 PWM and verify servo movement.
5. Confirm telemetry between flight controller and ground station (if used).

## Safety, testing, and legal considerations
- Follow local aviation laws and obtain necessary permissions to fly UAVs, especially near crowds.
- Never fly over people unless explicitly authorized and tested to be safe.
- Avoid using loud or startling mitigations that could cause panic; prefer passive observation and authorized crowd management coordination.
- Include fail‑safes: if GPS or communication fails, system should default to a safe state (no active interventions).
- Do not rely on this prototype for life‑critical decisions. Use only as an aid for human operators.

## Troubleshooting & common checks
- No camera stream: verify ESP‑CAM power, check serial logs for boot errors.
- GPS not fixing: ensure GPS antenna has sky view; verify 3.3V supply.
- Servo jitter: ensure grounds are common, check servo power (noise or undervoltage) and add a capacitor across 5V/GND near servo.
- Pico not booting: check VSYS power and USB connection; ensure power source is present.

## Contributing
Contributions welcome. Typical contributions:
- Improved schematics and an electrical diagram (KiCad / Eagle).
- PCB design for power distribution and connector consolidation.
- Firmware for the Pico and ESP‑CAM (with unit tests & README).
- Safety and legal compliance documentation for deployment.

To contribute:
1. Fork the repository
2. Add your changes on a feature branch
3. Open a pull request describing changes and testing steps

## License
This repository is provided under the MIT License.

## Contributors
Members: Kang Naeon, Choi Hyong Chan and Das Prithwis

