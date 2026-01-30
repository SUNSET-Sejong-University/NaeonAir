# 🎯 nCube-Thyme 게이트웨이 통합 명세서

## 프로젝트 개요

기존 게이트웨이(하드웨어 코드 + WebSocket 스트림)에 **nCube-Thyme-Nodejs**를 설치하여 IoT 디바이스를 Mobius 플랫폼에 자동 등록하는 통합 게이트웨이로 만듭니다.

---

## 📁 참고 자료

- **nCube-Thyme 레포**: https://github.com/IoTKETI/nCube-Thyme-Nodejs
- **Mobius4 레포**: https://github.com/IoTKETI/mobius4

---

## 🎯 목표

1. nCube-Thyme 설치 및 Mobius4와 연동 설정
2. 게이트웨이에 연결된 디바이스들을 Mobius에 자동 등록 (AE/CNT/CIN)
3. 기존 WebSocket 스트림 코드와 공존

---

## 📐 Mobius 리소스 구조 (필수 준수)

```
Mobius (CSE)
└── WisDrone (AE)
    └── device_{deviceId} (CNT)  ← 디바이스별 컨테이너
        ├── status (sub-CNT)       ← GPS, 배터리, 상태
        ├── crowd_analysis (sub-CNT) ← 군중 분석 데이터
        └── alerts (sub-CNT)       ← 알림/경고
```

### Device ID 형식
- `device_{random6chars}` (예: `device_a1b2c3`)
- 영소문자 + 숫자 6자리

---

## 🔧 구현 단계

### Step 1: nCube-Thyme 설치

```bash
# 게이트웨이 프로젝트에 nCube-Thyme 클론 또는 npm 설치
git clone https://github.com/IoTKETI/nCube-Thyme-Nodejs.git ncube
cd ncube
npm install
```

### Step 2: conf.js 설정

```javascript
// ncube/conf.js
conf.useprotocol = 'http';  // 또는 'mqtt'

// Mobius CSE 설정
cse.host = 'localhost';     // Mobius4 서버 IP
cse.port = '7599';          // Mobius4 HTTP 포트
cse.name = 'Mobius';        // CSE 이름 (대소문자 주의!)
cse.id = '/Mobius';

// AE 설정
ae.name = 'WisDrone';       // ⚠️ 프론트엔드와 동일해야 함
ae.id = 'S' + ae.name;
ae.parent = '/' + cse.name;
ae.appid = 'wisdrone';
ae.bodytype = 'json';

// Container 배열 - 디바이스별로 동적 생성 필요
// 기본값은 비워두고, 디바이스 감지 시 동적으로 추가
cnt_arr = [];
```

### Step 3: 디바이스 등록 로직 구현

게이트웨이에서 새 디바이스 감지 시:

```javascript
// 1. 메인 디바이스 컨테이너 생성
const deviceId = `device_${generateRandomId(6)}`;
createContainer(deviceId);

// 2. 서브 컨테이너 생성
createContainer(`${deviceId}/status`);
createContainer(`${deviceId}/crowd_analysis`);
createContainer(`${deviceId}/alerts`);

// 3. 초기 상태 데이터 전송
createContentInstance(`${deviceId}/status`, {
  position: { lat: 37.4979, lng: 127.0276, altitude: 50 },
  status: 'ACTIVE',
  battery: 100,
  timestamp: new Date().toISOString()
});
```

### Step 4: 주기적 데이터 전송

```javascript
// 5초마다 디바이스 상태 업데이트
setInterval(() => {
  devices.forEach(device => {
    createContentInstance(`${device.id}/status`, {
      position: device.getGPS(),
      status: device.getStatus(),
      battery: device.getBattery(),
      timestamp: new Date().toISOString()
    });
  });
}, 5000);
```

### Step 5: 기존 WebSocket 코드 통합

- nCube-Thyme과 기존 WebSocket 스트림 서버가 충돌하지 않도록 포트 분리
- 또는 단일 서버에서 두 기능 모두 처리

---

## ✅ 검증 체크리스트

- [ ] nCube-Thyme 설치 완료
- [ ] `conf.js`에 Mobius4 주소/포트/CSE이름 설정
- [ ] 게이트웨이 시작 시 Mobius에 AE 등록 확인
- [ ] 디바이스 감지 시 `device_{id}` 컨테이너 생성 확인
- [ ] 서브 컨테이너 (status, crowd_analysis, alerts) 생성 확인
- [ ] 주기적 CIN 데이터 전송 확인
- [ ] 프론트엔드에서 `discoverDevices()` 호출 시 디바이스 목록 조회 확인

---

## ⚠️ 주의사항

1. **CSE 이름 대소문자 구분**: `Mobius` ≠ `mobius`
2. **AE 이름 일치**: 게이트웨이와 프론트엔드가 동일한 AE(`WisDrone`) 사용
3. **Container 이름 형식**: 반드시 `device_` prefix 사용 (프론트에서 필터링)
4. **oneM2M 헤더**:
   - `X-M2M-Origin`: `SM` (Admin) 또는 AEI
   - `X-M2M-RVI`: `4`
   - `Content-Type`: `application/json;ty=3` (CNT) 또는 `ty=4` (CIN)

---

## 📞 프론트엔드 연동 API

프론트엔드는 다음 함수로 Mobius 데이터를 조회합니다:

| 함수 | 용도 |
|------|------|
| `discoverDevices()` | AE 하위 device_* 컨테이너 목록 조회 |
| `getDeviceLatestData(deviceId, 'status')` | 디바이스 최신 상태 조회 |
| `getDeviceLatestData(deviceId, 'crowd_analysis')` | 군중 분석 데이터 조회 |
| `getDeviceLatestData(deviceId, 'alerts')` | 알림 데이터 조회 |

게이트웨이가 올바르게 데이터를 등록하면 프론트엔드에서 자동으로 조회됩니다.
