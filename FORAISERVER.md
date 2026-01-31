# 🤖 AI 서버 통신 명세서 (FORAISERVER)

> AI 서버 개발자를 위한 게이트웨이 연동 가이드

---

## 개요

AI 서버는 **게이트웨이로부터 데이터를 수신만** 합니다 (단방향 통신).  
게이트웨이가 10초 간격으로 드론 프레임을 AI 서버로 전송합니다.

```
┌──────────┐    HTTP POST    ┌──────────┐
│ Gateway  │ ──────────────▶ │ AI Server│
└──────────┘   (10초 간격)    └──────────┘
     │
     ├── files: { file: frame.jpg }
     └── data:  { device_id: "device_a1b2c3" }
```

---

## 1. 게이트웨이 → AI 서버 통신

### 엔드포인트

```
POST /analyze
Content-Type: multipart/form-data
```

### 요청 형식

| 필드 | 타입 | 설명 |
|------|------|------|
| `file` | `file` (binary) | JPEG 이미지 프레임 |
| `device_id` | `string` | 디바이스 ID (예: `device_a1b2c3`) |

### Python 요청 예시 (게이트웨이 코드 참고)

```python
import requests

files = {"file": ("frame.jpg", frame_bytes, "image/jpeg")}
data = {"device_id": "device_a1b2c3"}

response = requests.post(
    "http://AI_SERVER_IP:8000/analyze",
    files=files,
    data=data,
    timeout=2
)
```

### AI 서버 수신 예시 (FastAPI)

```python
from fastapi import FastAPI, File, UploadFile, Form

app = FastAPI()

@app.post("/analyze")
async def analyze_frame(
    file: UploadFile = File(...),
    device_id: str = Form(...)
):
    # 이미지 처리
    frame_bytes = await file.read()
    
    # AI 분석 수행
    result = your_ai_model.analyze(frame_bytes)
    
    # 결과 반환 또는 Mobius에 저장
    return {"device_id": device_id, "result": result}
```

---

## 2. Mobius 리소스 구조 (AI 결과 저장용)

게이트웨이가 디바이스 등록 시 아래 구조를 자동으로 생성합니다.

```
Mobius (CSE)
└── WisDrone (AE)
    └── device_{deviceId} (CNT)
        ├── status (sub-CNT)         ← GPS, 배터리, 상태
        ├── crowd_analysis (sub-CNT) ← 🎯 AI 분석 결과 저장 위치
        └── alerts (sub-CNT)         ← 알림/경고
```

### 하드코딩 가능한 정보

| 항목 | 값 | 설명 |
|------|-----|------|
| Mobius CSE | `Mobius` | 고정 |
| AE 이름 | `WisDrone` | 고정 |
| 메인 CNT | `device_{deviceId}` | **deviceId만 변수** |
| 결과 저장 CNT | `crowd_analysis` | 고정 |
| 상태 CNT | `status` | 고정 |
| 알림 CNT | `alerts` | 고정 |

### Device ID 형식

```
device_{random6chars}
```

**예시**: `device_a1b2c3`, `device_123456`

---

## 3. AI 분석 결과를 Mobius에 저장하기

AI 서버가 분석 결과를 Mobius에 저장하려면 HTTP POST 요청을 보냅니다.

### Mobius 접속 정보

| 항목 | 값 |
|------|-----|
| Host | `localhost` (또는 Mobius 서버 IP) |
| Port | `7599` |
| Base URL | `http://{host}:7599` |

### CIN (Content Instance) 생성 요청

```
POST /Mobius/WisDrone/device_{deviceId}/crowd_analysis
Content-Type: application/json;ty=4
X-M2M-Origin: SWisDrone
X-M2M-RI: {unique_request_id}
```

### 요청 Body

```json
{
    "m2m:cin": {
        "con": {
            "timestamp": "2026-01-31T01:30:00+09:00",
            "crowd_count": 42,
            "density": "medium",
            "anomaly": false,
            "device_id": "device_a1b2c3"
        }
    }
}
```

### Python 예시 (AI 결과 저장)

```python
import requests
import json
from datetime import datetime

def save_to_mobius(device_id: str, analysis_result: dict):
    """AI 분석 결과를 Mobius에 저장"""
    
    MOBIUS_HOST = "localhost"  # Mobius 서버 주소
    MOBIUS_PORT = 7599
    
    url = f"http://{MOBIUS_HOST}:{MOBIUS_PORT}/Mobius/WisDrone/{device_id}/crowd_analysis"
    
    headers = {
        "Content-Type": "application/json;ty=4",
        "X-M2M-Origin": "SWisDrone",
        "X-M2M-RI": f"req_{datetime.now().timestamp()}"
    }
    
    payload = {
        "m2m:cin": {
            "con": json.dumps({
                "timestamp": datetime.now().isoformat(),
                "device_id": device_id,
                **analysis_result  # crowd_count, density 등
            })
        }
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=5)
    return response.status_code == 201
```

---

## 4. 전체 플로우

```
1. 드론 → 게이트웨이: 영상 프레임 전송 (WebSocket)

2. 게이트웨이 → AI 서버: 10초마다 프레임 전송 (HTTP POST)
   - file: frame.jpg
   - device_id: "device_xxx"

3. AI 서버: 군중 분석 수행

4. AI 서버 → Mobius: 분석 결과 저장 (HTTP POST)
   - URL: /Mobius/WisDrone/{device_id}/crowd_analysis
   
5. 프론트엔드 ← Mobius: 분석 결과 조회 (선택적)
```

---

## 5. 요약: AI 서버가 알아야 할 것

### ✅ 받는 데이터 (게이트웨이에서)
- **엔드포인트**: `POST /analyze`
- **데이터**: `file` (이미지), `device_id` (문자열)

### ✅ 보내는 데이터 (Mobius로)
- **Mobius URL**: `http://{MOBIUS_HOST}:7599`
- **경로 패턴**: `/Mobius/WisDrone/{device_id}/crowd_analysis`
- **device_id만 변수**, 나머지는 하드코딩 OK

### ✅ 하드코딩 값
```python
# AI 서버 설정
MOBIUS_CSE = "Mobius"
MOBIUS_AE = "WisDrone"
MOBIUS_PORT = 7599
SUB_CNT_ANALYSIS = "crowd_analysis"
SUB_CNT_STATUS = "status"
SUB_CNT_ALERTS = "alerts"

# 경로 생성
def get_analysis_path(device_id):
    return f"/Mobius/WisDrone/{device_id}/crowd_analysis"
```

---

## 6. 테스트용 비디오 시뮬레이터

드론 카메라가 없거나 테스트 환경에서 사용할 수 있는 비디오 파일 기반 시뮬레이터입니다.

### 비디오 파일 준비

```bash
# 테스트 비디오 폴더
ground-control/test_videos/
```

이 폴더에 테스트용 비디오 파일 (.mp4, .avi, .mov 등)을 넣습니다.

### 실행 방법

```bash
cd ground-control
source venv/bin/activate

# 기본 사용 (첫 번째 비디오 자동 선택)
python3 video_simulator.py

# 특정 비디오 지정
python3 video_simulator.py drone_footage.mp4

# 비디오 목록 보기
python3 video_simulator.py --list

# 모든 비디오 동시 스트리밍 (여러 드론 시뮬레이션)
python3 video_simulator.py --all

# 한 번만 재생 (루프 없음)
python3 video_simulator.py test.mp4 --no-loop
```

### 작동 방식

```
┌─────────────────┐         ┌──────────┐         ┌──────────┐
│ Video File      │  JPEG   │ Gateway  │  HTTP   │ AI Server│
│ (.mp4, .avi...) │ ──────▶ │ :3001    │ ──────▶ │ /analyze │
└─────────────────┘         └──────────┘         └──────────┘
```

1. OpenCV로 비디오 프레임을 읽음
2. 각 프레임을 JPEG로 인코딩
3. 게이트웨이로 WebSocket 전송 (실제 드론처럼 작동)
4. 게이트웨이가 10초 간격으로 AI 서버에 전송

### 의존성

```bash
source venv/bin/activate
pip install opencv-python websockets
```

---

## 참고

- [GATEWAY_SPEC.md](./GATEWAY_SPEC.md) - 게이트웨이 전체 명세
- [nCube 설정](./ground-control/ncube/conf.js) - Mobius 연결 설정
- [gateway.py](./ground-control/gateway.py) - AI 전송 로직 (line 78-86)
- [video_simulator.py](./ground-control/video_simulator.py) - 비디오 테스트 시뮬레이터
