/**
 * WisDrone Device Manager
 * 
 * 디바이스 연결/해제 관리 및 Mobius 자동 등록
 * 
 * 기능:
 * - 연결된 디바이스 추적 (deviceId ↔ WebSocket 매핑)
 * - 5초 주기 상태 체크
 * - Mobius 컨테이너 자동 생성
 */

const deviceHandler = require('./ncube/device_handler');

// ==========================================
// Device Registry
// ==========================================
const devices = new Map();
// { deviceId: { ws: WebSocket, status: 'active'|'inactive', lastSeen: Date, port: number } }

// 다음 사용 가능한 내부 인덱스
let deviceIndex = 0;

// ==========================================
// Device ID 생성
// ==========================================
function generateDeviceId() {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let id = '';
    for (let i = 0; i < 6; i++) {
        id += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return `device_${id}`;
}

// ==========================================
// 디바이스 등록
// ==========================================
async function registerDevice(ws, providedId = null) {
    const deviceId = providedId || generateDeviceId();
    
    // 이미 등록된 경우
    if (devices.has(deviceId)) {
        const device = devices.get(deviceId);
        device.ws = ws;
        device.status = 'active';
        device.lastSeen = new Date();
        console.log(`♻️ Device reconnected: ${deviceId}`);
        return deviceId;
    }
    
    // 새 디바이스 등록
    devices.set(deviceId, {
        ws: ws,
        status: 'active',
        lastSeen: new Date(),
        index: deviceIndex++,
    });
    
    // Mobius 컨테이너 생성
    try {
        await deviceHandler.registerDevice(deviceId);
        console.log(`✅ Device registered: ${deviceId}`);
    } catch (error) {
        console.error(`⚠️ Mobius registration failed for ${deviceId}:`, error.message);
        // Mobius 실패해도 디바이스는 등록 유지
    }
    
    return deviceId;
}

// ==========================================
// 디바이스 해제
// ==========================================
function unregisterDevice(deviceId) {
    if (devices.has(deviceId)) {
        const device = devices.get(deviceId);
        device.status = 'inactive';
        device.ws = null;
        console.log(`📴 Device disconnected: ${deviceId}`);
        return true;
    }
    return false;
}

// ==========================================
// 디바이스 조회
// ==========================================
function getDevice(deviceId) {
    return devices.get(deviceId);
}

function getActiveDevices() {
    const active = [];
    devices.forEach((device, id) => {
        if (device.status === 'active') {
            active.push({
                id: id,
                index: device.index,
                lastSeen: device.lastSeen,
            });
        }
    });
    return active;
}

function getAllDevices() {
    const all = [];
    devices.forEach((device, id) => {
        all.push({
            id: id,
            status: device.status,
            index: device.index,
            lastSeen: device.lastSeen,
        });
    });
    return all;
}

// ==========================================
// 상태 체크 (5초 주기)
// ==========================================
const HEARTBEAT_TIMEOUT = 15000; // 15초 동안 응답 없으면 inactive

function startHealthCheck() {
    setInterval(() => {
        const now = Date.now();
        devices.forEach((device, id) => {
            if (device.status === 'active') {
                const elapsed = now - device.lastSeen.getTime();
                if (elapsed > HEARTBEAT_TIMEOUT) {
                    device.status = 'inactive';
                    device.ws = null;
                    console.log(`⚠️ Device timeout: ${id}`);
                }
            }
        });
    }, 5000);
    
    console.log('💓 Health check started (5s interval)');
}

// ==========================================
// Heartbeat 업데이트
// ==========================================
function updateHeartbeat(deviceId) {
    const device = devices.get(deviceId);
    if (device) {
        device.lastSeen = new Date();
        device.status = 'active';
    }
}

// ==========================================
// WebSocket으로 deviceId 찾기
// ==========================================
function findDeviceByWs(ws) {
    for (const [id, device] of devices) {
        if (device.ws === ws) {
            return id;
        }
    }
    return null;
}

// ==========================================
// Export
// ==========================================
module.exports = {
    registerDevice,
    unregisterDevice,
    getDevice,
    getActiveDevices,
    getAllDevices,
    startHealthCheck,
    updateHeartbeat,
    findDeviceByWs,
    generateDeviceId,
};

// ==========================================
// CLI Test
// ==========================================
if (require.main === module) {
    (async () => {
        console.log('🧪 Testing device_manager...');
        
        // Mock WebSocket
        const mockWs = { send: () => {} };
        
        // 디바이스 등록
        const id1 = await registerDevice(mockWs);
        const id2 = await registerDevice(mockWs);
        
        console.log('Active devices:', getActiveDevices());
        
        // 해제
        unregisterDevice(id1);
        console.log('After unregister:', getAllDevices());
    })();
}
