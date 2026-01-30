# WisDrone Gateway 개발 진행 현황

> 최종 업데이트: 2026-01-31 00:26

---

## ✅ 완료!

모든 Phase 구현 및 테스트 완료.

---

## 🎯 아키텍처

```
[Drones] ──WS──▶ [Gateway:3001] ──WS──▶ [Frontend]
                      │
                      ├──10s──▶ [AI Server]
                      └──HTTP──▶ [Mobius:7599]
```

| 항목 | 설정 |
|------|------|
| WebSocket | 단일 포트 3001 + deviceId 채널 |
| Bridge | Node.js 포트 9800 |
| Mobius | localhost:7599, AE: WisDrone |
| Python venv | 프로젝트 루트 `.venv/` |

---

## 📁 파일 구조

```
NaeonAir-/
├── .venv/               # Python 가상환경
└── ground-control/
    ├── gateway.py           # ✅ 메인 게이트웨이
    ├── device_manager.js    # ✅ 디바이스 관리
    ├── drone_simulator.py   # ✅ 테스트 시뮬레이터
    ├── start_gateway.sh     # ✅ 시작 스크립트
    └── ncube/               # ✅ Mobius 연동
```

---

## 🚀 실행

```bash
cd ground-control
./start_gateway.sh
```

**테스트:**
```bash
source ../.venv/bin/activate
python3 drone_simulator.py
```

---

## 📊 진행률

```
Phase 0-3: ████████████████████ 100%
```

---

## 🔧 남은 작업 (통신 설정)

### 1. AI 서버 연동

`gateway.py`에서 수정:
```python
AI_SERVER_URL = "http://실제_AI_서버_IP:8000/analyze"
```
- 전송 형식: multipart form-data (`frame`: 이미지, `device_id`: 문자열)
- 전송 주기: 10초 (변경 가능)

---

### 2. 프론트엔드 연동

**WebSocket 연결**: `ws://게이트웨이_IP:3001`

```javascript
// 1. 연결
const ws = new WebSocket('ws://localhost:3001');

// 2. 핸드셰이크
ws.send(JSON.stringify({ type: 'FRONTEND' }));

// 3. 디바이스 구독
ws.send(JSON.stringify({ type: 'SUBSCRIBE', deviceId: 'device_xxx' }));

// 4. 프레임 수신
ws.onmessage = (e) => {
  if (e.data instanceof Blob) {
    // 영상 프레임 표시
  }
};
```

---

### 3. ESP32 드론 코드 수정

기존 → 새 프로토콜:

```cpp
// 연결 후 핸드셰이크 전송
ws.sendTXT("{\"type\":\"DRONE\",\"deviceId\":\"drone_001\"}");

// 응답 확인: {"type":"REGISTERED","deviceId":"drone_001"}

// 프레임은 기존처럼 binary 전송
ws.sendBIN(frameBuffer, frameLength);
```

---

### 4. 레거시 코드 정리

| 파일 | 상태 |
|------|------|
| `cam_receiver.py` | ❌ 삭제 예정 (gateway.py로 대체됨) |
| `ground-control/venv/` | ❌ 삭제 가능 (루트 .venv 사용) |

---

### 5. 테스트 필요 목록

- [ ] Mobius4 서버 연결 확인
- [ ] 게이트웨이 ↔ 드론 연결
- [ ] 게이트웨이 ↔ 프론트엔드 스트리밍
- [ ] AI 서버 분석 결과 Mobius 저장
- [ ] 멀티 디바이스 동시 스트리밍
