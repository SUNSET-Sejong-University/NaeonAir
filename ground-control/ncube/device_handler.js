/**
 * WisDrone Device Handler for nCube-Thyme
 * 
 * 드론 디바이스를 Mobius에 자동 등록하고 데이터를 전송합니다.
 * GATEWAY_SPEC.md 규격에 따른 리소스 구조:
 *   WisDrone (AE)
 *     └── device_{id} (CNT)
 *         ├── status (sub-CNT)
 *         ├── crowd_analysis (sub-CNT)
 *         └── alerts (sub-CNT)
 */

const conf = require('./conf');
const http = require('http');

// ==========================================
// Configuration
// ==========================================
const MOBIUS_HOST = conf.cse.host;
const MOBIUS_PORT = conf.cse.port;
const CSE_NAME = conf.cse.name;
const AE_NAME = conf.ae.name;
// Mobius4 Admin Origin (AE 미등록 시에도 사용 가능)
const ADMIN_ORIGIN = 'SM';

// 등록된 디바이스 추적
const registeredDevices = new Set();

// ==========================================
// Helper: Generate Device ID
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
// oneM2M HTTP Request Helper
// ==========================================
function sendRequest(method, path, body, resourceType) {
    return new Promise((resolve, reject) => {
        const headers = {
            'X-M2M-RI': `req_${Date.now()}_${Math.random().toString(36).substring(7)}`,
            'X-M2M-Origin': ADMIN_ORIGIN,
            'X-M2M-RVI': '4',
            'Accept': 'application/json',
        };
        
        if (resourceType) {
            headers['Content-Type'] = `application/json;ty=${resourceType}`;
        }
        
        const options = {
            hostname: MOBIUS_HOST,
            port: MOBIUS_PORT,
            path: path,
            method: method,
            headers: headers,
        };
        
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                resolve({ status: res.statusCode, data: data ? JSON.parse(data) : null });
            });
        });
        
        req.on('error', reject);
        
        if (body) {
            req.write(JSON.stringify(body));
        }
        req.end();
    });
}

// ==========================================
// Container Creation
// ==========================================
async function createContainer(parentPath, containerName) {
    const path = `/${CSE_NAME}${parentPath}`;
    const body = {
        'm2m:cnt': {
            rn: containerName,
        }
    };
    
    try {
        const result = await sendRequest('POST', path, body, 3);
        if (result.status === 201) {
            console.log(`✅ Container created: ${containerName}`);
            return true;
        } else if (result.status === 409) {
            console.log(`⚠️ Container already exists: ${containerName}`);
            return true;
        } else {
            console.error(`❌ Container creation failed: ${result.status}`, result.data);
            return false;
        }
    } catch (error) {
        console.error(`❌ Container creation error: ${error.message}`);
        return false;
    }
}

// ==========================================
// Content Instance Creation
// ==========================================
async function createContentInstance(containerPath, data) {
    const path = `/${CSE_NAME}/${AE_NAME}${containerPath}`;
    const body = {
        'm2m:cin': {
            con: JSON.stringify(data),
        }
    };
    
    try {
        const result = await sendRequest('POST', path, body, 4);
        if (result.status === 201) {
            console.log(`📤 Data sent: ${containerPath}`);
            return true;
        } else {
            console.error(`❌ CIN creation failed: ${result.status}`);
            return false;
        }
    } catch (error) {
        console.error(`❌ CIN creation error: ${error.message}`);
        return false;
    }
}

// ==========================================
// Device Registration (GATEWAY_SPEC 규격)
// ==========================================
async function registerDevice(deviceId = null) {
    const id = deviceId || generateDeviceId();
    
    if (registeredDevices.has(id)) {
        console.log(`ℹ️ Device already registered: ${id}`);
        return id;
    }
    
    console.log(`🔧 Registering device: ${id}`);
    
    // 1. 메인 디바이스 컨테이너 생성
    const mainCreated = await createContainer(`/${AE_NAME}`, id);
    if (!mainCreated) {
        console.error(`❌ Failed to register device: ${id}`);
        return null;
    }
    
    // 2. 서브 컨테이너 생성 (GATEWAY_SPEC.md 규격)
    await createContainer(`/${AE_NAME}/${id}`, 'status');
    await createContainer(`/${AE_NAME}/${id}`, 'crowd_analysis');
    await createContainer(`/${AE_NAME}/${id}`, 'alerts');
    
    registeredDevices.add(id);
    console.log(`✅ Device registered: ${id}`);
    
    return id;
}

// ==========================================
// Send Device Status Data
// ==========================================
async function sendStatusData(deviceId, statusData) {
    const data = {
        position: statusData.position || { lat: 37.4979, lng: 127.0276, altitude: 50 },
        status: statusData.status || 'ACTIVE',
        battery: statusData.battery || 100,
        timestamp: new Date().toISOString(),
    };
    
    return await createContentInstance(`/${deviceId}/status`, data);
}

// ==========================================
// Send Crowd Analysis Data
// ==========================================
async function sendCrowdAnalysisData(deviceId, analysisData) {
    const data = {
        count: analysisData.count || 0,
        density: analysisData.density || 'LOW',
        timestamp: new Date().toISOString(),
    };
    
    return await createContentInstance(`/${deviceId}/crowd_analysis`, data);
}

// ==========================================
// Send Alert Data
// ==========================================
async function sendAlertData(deviceId, alertData) {
    const data = {
        type: alertData.type || 'INFO',
        message: alertData.message || '',
        timestamp: new Date().toISOString(),
    };
    
    return await createContentInstance(`/${deviceId}/alerts`, data);
}

// ==========================================
// Get Registered Devices
// ==========================================
function getRegisteredDevices() {
    return Array.from(registeredDevices);
}

// ==========================================
// Export Functions
// ==========================================
module.exports = {
    registerDevice,
    sendStatusData,
    sendCrowdAnalysisData,
    sendAlertData,
    getRegisteredDevices,
    generateDeviceId,
};

// ==========================================
// CLI Test Mode
// ==========================================
if (require.main === module) {
    (async () => {
        console.log('🧪 Testing device_handler...');
        
        // 테스트 디바이스 등록
        const deviceId = await registerDevice();
        
        if (deviceId) {
            // 테스트 데이터 전송
            await sendStatusData(deviceId, {
                position: { lat: 37.4979, lng: 127.0276, altitude: 100 },
                status: 'ACTIVE',
                battery: 85,
            });
            
            console.log('✅ Test complete. Device:', deviceId);
        }
    })();
}
