# 🎯 WisDrone Gateway 통합 명세서

> 📋 **현재 진행 상황**: [PROGRESS.md](./ground-control/PROGRESS.md) 참조

---

## 목표

게이트웨이가 **드론 디바이스를 Mobius에 자동 등록**하고, **실시간 영상 스트리밍**과 **AI 분석 연동**을 담당한다.

---

## 아키텍처

```
┌───────────────────────────────────────────────────────────────┐
│                    Gateway (Python + Node.js)                  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│   [드론들] ──WebSocket──▶ [Gateway] ──WebSocket──▶ [Frontend] │
│                              │                                │
│                              ├──10초 간격──▶ [AI Server]      │
│                              │                                │
│                              └──HTTP──▶ [Mobius4]             │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 핵심 결정사항

| 항목 | 결정 |
|------|------|
| WebSocket | **단일 포트 (3001) + deviceId 채널** |
| 디바이스 등록 | **시작 시 + 5초 주기 감지** |
| 데이터 흐름 | **스트리밍만 직접 WS, 나머지는 AI→Mobius** |

---

## Mobius 리소스 구조

```
Mobius (CSE)
└── WisDrone (AE)
    └── device_{deviceId} (CNT)
        ├── status (sub-CNT)         ← GPS, 배터리, 상태
        ├── crowd_analysis (sub-CNT) ← AI 분석 결과
        └── alerts (sub-CNT)         ← 알림/경고
```

**Device ID 형식**: `device_{random6chars}` (예: `device_a1b2c3`)

---

## 핵심 로직

### 1. 디바이스 등록
```
드론 연결 → deviceId 생성 → Mobius 컨테이너 생성
                          (device_*, status, crowd_analysis, alerts)
```

### 2. 스트리밍 라우팅
```
프론트엔드: { type: 'SUBSCRIBE', deviceId: 'device_xxx' }
게이트웨이: 해당 deviceId 프레임만 해당 클라이언트에 전송
```

### 3. AI 연동
```
10초 간격: 프레임 + deviceId → AI 서버
AI 결과 → Mobius crowd_analysis 컨테이너 저장
```

---

## 파일 구조

```
ground-control/
├── gateway.py           # 메인 게이트웨이 (WebSocket 라우팅)
├── device_manager.js    # 디바이스 관리 (등록/감지)
├── start_gateway.sh     # 시작 스크립트
└── ncube/               # nCube-Thyme (Mobius 연동)
    ├── conf.js          # 설정 (포트 7599, AE: WisDrone)
    ├── device_handler.js
    └── gateway_bridge.js
```

---

## 참고 자료

- **nCube-Thyme**: https://github.com/IoTKETI/nCube-Thyme-Nodejs
- **Mobius4**: https://github.com/IoTKETI/mobius4
- **프론트엔드**: `/Users/hyhchan/Desktop/wisdrone-interface/` (수정 금지)
