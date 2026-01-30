# WisDrone Gateway

nCube-Thyme integration for Mobius4 IoT platform.

nCube-Thyme 기반 Mobius4 IoT 플랫폼 연동 게이트웨이.

---

## Quick Start / 빠른 시작

### macOS

```bash
# 1. Setup Python venv (first time only / 최초 1회만)
cd NaeonAir-
python3 -m venv .venv
source .venv/bin/activate
pip install requests websockets

# 2. Install Node dependencies / Node 의존성 설치
cd ground-control/ncube && npm install && cd ..

# 3. Run gateway / 게이트웨이 실행
./start_gateway.sh
```

### Linux (Ubuntu/Debian)

```bash
# 1. Install requirements / 필수 패키지 설치
sudo apt update
sudo apt install -y python3-venv nodejs npm

# 2. Setup Python venv / Python 가상환경 설정
cd NaeonAir-
python3 -m venv .venv
source .venv/bin/activate
pip install requests websockets

# 3. Install Node dependencies / Node 의존성 설치
cd ground-control/ncube && npm install && cd ..

# 4. Run gateway / 게이트웨이 실행
chmod +x start_gateway.sh
./start_gateway.sh
```

---

## Ports / 포트

| Service | Port | Description |
|---------|------|-------------|
| WebSocket Gateway | 3001 | Drone ↔ Frontend streaming |
| Node.js Bridge | 9800 | Mobius API bridge |
| Mobius4 | 7599 | IoT platform |

---

## API Endpoints / API 엔드포인트

### WebSocket (ws://localhost:3001)

| Message | Description |
|---------|-------------|
| `{ type: 'DRONE', deviceId: 'xxx' }` | Drone handshake / 드론 연결 |
| `{ type: 'FRONTEND' }` | Frontend handshake / 프론트엔드 연결 |
| `{ type: 'SUBSCRIBE', deviceId: 'xxx' }` | Subscribe to device / 디바이스 구독 |

### HTTP Bridge (http://localhost:9800)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | Register device / 디바이스 등록 |
| `/status` | POST | Send status / 상태 전송 |
| `/devices` | GET | List devices / 디바이스 목록 |
| `/health` | GET | Health check / 상태 확인 |

---

## Test / 테스트

```bash
source .venv/bin/activate
cd ground-control
python3 drone_simulator.py
```
