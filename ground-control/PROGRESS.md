# WisDrone Gateway 개발 진행 현황

> 최종 업데이트: 2026-01-30 23:53

---

## 🎯 아키텍처 결정사항

| 항목 | 결정 |
|------|------|
| **WebSocket** | 단일 포트 (3001) + deviceId 채널 |
| **디바이스 등록** | 시작 시 + 5초 주기 감지 |
| **데이터 흐름** | 스트리밍만 직접 WS → Frontend, 나머지는 AI → Mobius |

---

## ✅ Phase 0: nCube-Thyme 통합 (완료)

- [x] nCube-Thyme 설치 (`ground-control/ncube/`)
- [x] `conf.js` Mobius4 설정 (포트 7599, AE: WisDrone)
- [x] `device_handler.js` - Mobius 컨테이너 생성
- [x] `gateway_bridge.js` - HTTP 브릿지
- [x] 검증 완료

---

## 🔲 Phase 1: Device Manager (다음)

- [ ] `device_manager.js` 생성
  - 디바이스 연결/해제 관리
  - 5초 주기 상태 체크
  - Mobius 자동 등록 연동

---

## � Phase 2: WebSocket Router

- [ ] `gateway.py` 생성 (cam_receiver.py 대체)
  - 단일 포트 멀티 디바이스 라우팅
  - 프론트엔드 구독 처리: `{ type: 'SUBSCRIBE', deviceId }`
  - deviceId 기반 프레임 라우팅

---

## 🔲 Phase 3: AI Server 연동

- [ ] 10초 간격 프레임 + deviceId 전송
- [ ] 분석 결과 Mobius 저장

---

## 📁 파일 구조 (계획)

```
ground-control/
├── gateway.py              # [NEW] 메인 게이트웨이
├── device_manager.js       # [NEW] 디바이스 관리
├── start_gateway.sh        # 시작 스크립트
├── cam_receiver.py         # [DELETE] gateway.py로 대체
└── ncube/                  # ✅ 완료
    ├── conf.js
    ├── device_handler.js
    └── gateway_bridge.js
```

---

## � 진행률

```
Phase 0: ████████████████████ 100%
Phase 1: ░░░░░░░░░░░░░░░░░░░░   0%
Phase 2: ░░░░░░░░░░░░░░░░░░░░   0%
Phase 3: ░░░░░░░░░░░░░░░░░░░░   0%
----------------------------------------
Total:   █████░░░░░░░░░░░░░░░  25%
```
