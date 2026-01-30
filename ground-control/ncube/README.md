# WisDrone Gateway (nCube-Thyme Integration)

## 개요

기존 WebSocket 스트리밍 서버(`cam_receiver.py`)와 연동하여 드론 디바이스를 Mobius4 플랫폼에 자동 등록합니다.

## 디렉토리 구조

```
ground-control/
├── cam_receiver.py      # WebSocket 서버 (영상 스트림)
├── start_gateway.sh     # 게이트웨이 시작 스크립트
└── ncube/               # nCube-Thyme
    ├── conf.js          # Mobius 설정 (수정됨)
    ├── device_handler.js # 디바이스 등록/데이터 전송
    └── gateway_bridge.js # Python 연동용 HTTP 브릿지
```

## 설정

`ncube/conf.js`:
- **CSE**: `localhost:7599` (Mobius4)
- **AE**: `WisDrone`

## 실행

```bash
# 게이트웨이 시작
./start_gateway.sh

# 또는 직접 실행
cd ncube && node gateway_bridge.js
```

## API

| Endpoint | Method | 설명 |
|----------|--------|------|
| `/register` | POST | 디바이스 등록 |
| `/status` | POST | 상태 데이터 전송 |
| `/crowd` | POST | 군중 분석 데이터 |
| `/alert` | POST | 알림 전송 |
| `/devices` | GET | 등록된 디바이스 목록 |
| `/health` | GET | 헬스 체크 |

## Python 연동 예시

```python
import requests

BRIDGE_URL = "http://localhost:9800"

# 디바이스 등록
resp = requests.post(f"{BRIDGE_URL}/register")
device_id = resp.json()["deviceId"]

# 상태 전송
requests.post(f"{BRIDGE_URL}/status", json={
    "deviceId": device_id,
    "position": {"lat": 37.4979, "lng": 127.0276, "altitude": 50},
    "status": "ACTIVE",
    "battery": 85
})
```
