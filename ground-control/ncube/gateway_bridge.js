#!/usr/bin/env node
/**
 * WisDrone Gateway - nCube-Thyme Integration
 * 
 * 이 스크립트는 다음을 수행합니다:
 * 1. Mobius에 WisDrone AE 등록
 * 2. 드론 디바이스 자동 등록
 * 3. HTTP 서버로 Python WebSocket 서버와 연동
 */

const http = require('http');
const url = require('url');
const deviceHandler = require('./device_handler');
const conf = require('./conf');

const BRIDGE_PORT = 9800;

// ==========================================
// HTTP Bridge Server (Python 연동용)
// ==========================================
const server = http.createServer(async (req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const path = parsedUrl.pathname;
    
    // CORS 설정
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');
    
    // ==========================================
    // POST /register - 새 디바이스 등록
    // ==========================================
    if (path === '/register' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            try {
                const data = body ? JSON.parse(body) : {};
                const deviceId = await deviceHandler.registerDevice(data.deviceId);
                
                if (deviceId) {
                    res.writeHead(201);
                    res.end(JSON.stringify({ success: true, deviceId }));
                } else {
                    res.writeHead(500);
                    res.end(JSON.stringify({ success: false, error: 'Registration failed' }));
                }
            } catch (error) {
                res.writeHead(400);
                res.end(JSON.stringify({ success: false, error: error.message }));
            }
        });
        return;
    }
    
    // ==========================================
    // POST /status - 디바이스 상태 전송
    // ==========================================
    if (path === '/status' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const success = await deviceHandler.sendStatusData(data.deviceId, data);
                
                res.writeHead(success ? 200 : 500);
                res.end(JSON.stringify({ success }));
            } catch (error) {
                res.writeHead(400);
                res.end(JSON.stringify({ success: false, error: error.message }));
            }
        });
        return;
    }
    
    // ==========================================
    // POST /crowd - 군중 분석 데이터 전송
    // ==========================================
    if (path === '/crowd' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const success = await deviceHandler.sendCrowdAnalysisData(data.deviceId, data);
                
                res.writeHead(success ? 200 : 500);
                res.end(JSON.stringify({ success }));
            } catch (error) {
                res.writeHead(400);
                res.end(JSON.stringify({ success: false, error: error.message }));
            }
        });
        return;
    }
    
    // ==========================================
    // POST /alert - 알림 전송
    // ==========================================
    if (path === '/alert' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', async () => {
            try {
                const data = JSON.parse(body);
                const success = await deviceHandler.sendAlertData(data.deviceId, data);
                
                res.writeHead(success ? 200 : 500);
                res.end(JSON.stringify({ success }));
            } catch (error) {
                res.writeHead(400);
                res.end(JSON.stringify({ success: false, error: error.message }));
            }
        });
        return;
    }
    
    // ==========================================
    // GET /devices - 등록된 디바이스 목록
    // ==========================================
    if (path === '/devices' && req.method === 'GET') {
        const devices = deviceHandler.getRegisteredDevices();
        res.writeHead(200);
        res.end(JSON.stringify({ devices }));
        return;
    }
    
    // ==========================================
    // GET /health - 헬스체크
    // ==========================================
    if (path === '/health' && req.method === 'GET') {
        res.writeHead(200);
        res.end(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }));
        return;
    }
    
    // 404
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not Found' }));
});

// ==========================================
// Start Server
// ==========================================
server.listen(BRIDGE_PORT, () => {
    console.log('==========================================');
    console.log('🚀 WisDrone Gateway Bridge Started');
    console.log(`📡 Bridge Port: ${BRIDGE_PORT}`);
    console.log(`🎯 Mobius: ${conf.cse.host}:${conf.cse.port}`);
    console.log(`📦 AE: ${conf.ae.name}`);
    console.log('==========================================');
    console.log('');
    console.log('API Endpoints:');
    console.log('  POST /register  - 디바이스 등록');
    console.log('  POST /status    - 상태 데이터 전송');
    console.log('  POST /crowd     - 군중 분석 데이터');
    console.log('  POST /alert     - 알림 전송');
    console.log('  GET  /devices   - 등록된 디바이스 목록');
    console.log('  GET  /health    - 헬스 체크');
    console.log('==========================================');
});
