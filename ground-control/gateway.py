"""
WisDrone Gateway - Multi-Device WebSocket Router

기능:
1. 드론 연결: 실시간 프레임 수신
2. 프론트엔드 연결: deviceId 기반 구독/스트리밍
3. AI 서버: 10초 간격 프레임 전송
"""

import asyncio
import json
import time
import requests
from websockets.server import serve
from functools import partial

# ==========================================
# Configuration
# ==========================================
WS_PORT = 3001
AI_SERVER_URL = "http://172.16.10.64:8000/analyze"  # AI 서버 주소 (로컬)
AI_GPS_URL = "http://172.16.10.64:7599/gps"         # AI 서버 GPS 엔드포인트
AI_SEND_INTERVAL = 10.0  # 10초 간격
DEVICE_MANAGER_URL = "http://localhost:9800"  # Node.js bridge

# ==========================================
# State Management
# ==========================================
# 연결된 드론들 { device_id: websocket }
drone_connections = {}

# 연결된 프론트엔드 { websocket: subscribed_device_id }
frontend_subscriptions = {}

# 각 디바이스별 마지막 프레임 (AI 전송용)
last_frames = {}

# 마지막 AI 전송 시간
last_ai_send_time = {}


# ==========================================
# Device Registration (Node.js Bridge 연동)
# ==========================================
def register_device_to_mobius(device_id):
    """Node.js bridge를 통해 Mobius에 디바이스 등록"""
    try:
        resp = requests.post(
            f"{DEVICE_MANAGER_URL}/register",
            json={"deviceId": device_id},
            timeout=5
        )
        if resp.status_code == 201:
            print(f"✅ Registered to Mobius: {device_id}")
            return True
        else:
            print(f"⚠️ Mobius registration failed: {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Mobius bridge error: {e}")
        return False


def send_status_to_mobius(device_id, status_data):
    """디바이스 상태를 Mobius에 저장"""
    try:
        requests.post(
            f"{DEVICE_MANAGER_URL}/status",
            json={"deviceId": device_id, **status_data},
            timeout=2
        )
    except Exception as e:
        print(f"⚠️ Status send failed: {e}")


# ==========================================
# AI Server Integration
# ==========================================
def send_frame_to_ai(device_id, frame_bytes):
    """프레임을 AI 서버로 전송"""
    try:
        files = {"file": ("frame.jpg", frame_bytes, "image/jpeg")}
        data = {"device_id": device_id}
        response = requests.post(AI_SERVER_URL, files=files, data=data, timeout=2)
        print(f"📸 AI: {device_id} → {response.status_code}")
    except Exception as e:
        print(f"⚠️ AI send failed: {e}")


def send_gps_to_ai(device_id, gps_data):
    """GPS 데이터를 AI 서버로 전송"""
    try:
        payload = {"device_id": device_id, **gps_data}
        response = requests.post(AI_GPS_URL, json=payload, timeout=2)
        print(f"📍 GPS: {device_id} → {response.status_code}")
    except Exception as e:
        print(f"⚠️ GPS send failed: {e}")


# ==========================================
# Frame Router
# ==========================================
async def route_frame_to_subscribers(device_id, frame_bytes):
    """특정 디바이스의 프레임을 구독 중인 프론트엔드에 전송"""
    for ws, subscribed_id in list(frontend_subscriptions.items()):
        if subscribed_id == device_id:
            try:
                await ws.send(frame_bytes)
            except Exception:
                # 연결 끊김
                del frontend_subscriptions[ws]


# ==========================================
# WebSocket Handler
# ==========================================
async def handler(websocket):
    """메인 WebSocket 핸들러"""
    client_type = None
    device_id = None
    
    print(f"🔌 New connection from: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            # -------------------------------------------------
            # Text Message: Handshake / Control
            # -------------------------------------------------
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    # 드론 핸드셰이크
                    if msg_type == "DRONE":
                        device_id = data.get("deviceId")
                        if not device_id:
                            # ID 없으면 자동 생성
                            device_id = f"device_{int(time.time()) % 1000000:06d}"
                        
                        client_type = "drone"
                        drone_connections[device_id] = websocket
                        
                        # Mobius 등록
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, register_device_to_mobius, device_id)
                        
                        # 응답
                        await websocket.send(json.dumps({
                            "type": "REGISTERED",
                            "deviceId": device_id
                        }))
                        print(f"🚁 Drone connected: {device_id}")
                    
                    # 프론트엔드 핸드셰이크
                    elif msg_type == "BROWSER" or msg_type == "FRONTEND":
                        client_type = "frontend"
                        frontend_subscriptions[websocket] = None
                        await websocket.send(json.dumps({
                            "type": "CONNECTED",
                            "devices": list(drone_connections.keys())
                        }))
                        print(f"🖥️ Frontend connected")
                    
                    # 구독 요청
                    elif msg_type == "SUBSCRIBE":
                        target_id = data.get("deviceId")
                        if websocket in frontend_subscriptions:
                            frontend_subscriptions[websocket] = target_id
                            await websocket.send(json.dumps({
                                "type": "SUBSCRIBED",
                                "deviceId": target_id
                            }))
                            print(f"📺 Subscribed to: {target_id}")
                    
                    # 디바이스 목록 요청
                    elif msg_type == "LIST_DEVICES":
                        await websocket.send(json.dumps({
                            "type": "DEVICE_LIST",
                            "devices": list(drone_connections.keys())
                        }))
                    
                    # GPS 데이터 수신 (드론에서)
                    elif msg_type == "GPS" and client_type == "drone":
                        gps_data = {
                            "lat": data.get("lat", 0.0),
                            "lng": data.get("lng", 0.0),
                            "altitude": data.get("altitude", 50.0),
                            "battery": data.get("battery", 100.0),
                            "heading": data.get("heading", 0.0),
                            "speed": data.get("speed", 0.0)
                        }
                        # AI 서버로 전송 (비동기)
                        loop = asyncio.get_running_loop()
                        loop.run_in_executor(
                            None, 
                            partial(send_gps_to_ai, device_id, gps_data)
                        )
                
                except json.JSONDecodeError:
                    # 레거시: "BROWSER" 문자열
                    if message == "BROWSER":
                        client_type = "frontend"
                        frontend_subscriptions[websocket] = None
                        print(f"🖥️ Frontend connected (legacy)")
            
            # -------------------------------------------------
            # Binary Message: Frame from Drone
            # -------------------------------------------------
            elif isinstance(message, bytes) and client_type == "drone":
                current_time = time.time()
                
                # 1. 구독자에게 프레임 전송
                await route_frame_to_subscribers(device_id, message)
                
                # 2. 최신 프레임 저장
                last_frames[device_id] = message
                
                # 3. AI 서버로 전송 (10초 간격)
                last_send = last_ai_send_time.get(device_id, 0)
                if current_time - last_send >= AI_SEND_INTERVAL:
                    last_ai_send_time[device_id] = current_time
                    loop = asyncio.get_running_loop()
                    loop.run_in_executor(
                        None, 
                        partial(send_frame_to_ai, device_id, message)
                    )
    
    except Exception as e:
        print(f"⚠️ Connection error: {e}")
    
    finally:
        # 연결 해제 처리
        if client_type == "drone" and device_id:
            if device_id in drone_connections:
                del drone_connections[device_id]
            print(f"🚁 Drone disconnected: {device_id}")
        
        elif client_type == "frontend":
            if websocket in frontend_subscriptions:
                del frontend_subscriptions[websocket]
            print(f"🖥️ Frontend disconnected")

# ==========================================
# Pico TCP Telemetry Integration (미구현)
# ==========================================
async def handle_pico_telemetry(reader, writer):
    """we handle raw TCP GPS data from the Raspberry Pi Pico 2W on port 3002"""
    device_id = "pico_telemetry"
    loop = asyncio.get_running_loop()  # keep the loop running for background tasks
    print("Pico Telemtry connected to Port 3002")

    try:
        while True:
            data  = await reader.readline()
            if not data:
                break

            message = data.decode().strip()
            # we parse the GPS,lat,lon,alt string
            if message.startswith("GPS"):
                parts = message.split(",")
                if len(parts) == 4:
                    gps_data = {
                        "lat": float(parts[1]),
                        "lng": float(parts[2]),
                        "altitude": float(parts[3]),
                    }
                    # send to AI server
                    loop.run_in_executor(None, partial(send_gps_to_ai, device_id, gps_data))  # run in background

                    # forward to mobius
                    loop.run_in_executor(None, partial(send_status_to_mobius, device_id, gps_data)) # run in background

                    print(f"📍 Relayed GPS from Pico: {gps_data['lat']}, {gps_data['lng']}")

    except Exception as e:
        print(f"⚠️ Pico Telemetry error: {e}")
    finally:
        print("Pico Telemetry disconnected")
        writer.close()
        await writer.wait_closed()


# ==========================================
# Main
# ==========================================
async def main():
    ws_server = serve(handler, "0.0.0.0", WS_PORT)  # start the websocket server (port 3001)
    pico_server = await asyncio.start_server(handle_pico_telemetry, "0.0.0.0", 3002) # start the pico telemetry server (port 3002)
    
    print("==========================================")
    print("🚀 WisDrone Gateway Running")
    print(f"📡 WebSocket Port: {WS_PORT}")
    print(f"📡 TCP (Telemetry) Port: 3002")
    print(f"🤖 AI Server: {AI_SERVER_URL}")
    print(f"⏱️ AI Send Interval: {AI_SEND_INTERVAL}s")
    print("==========================================")
    print("")
    print("Protocol:")
    print("  Drone  → { type: 'DRONE', deviceId: 'xxx' }")
    print("  Frontend → { type: 'FRONTEND' }")
    print("  Subscribe → { type: 'SUBSCRIBE', deviceId: 'xxx' }")
    print("==========================================")

    async with ws_server:
        await asyncio.gather(
            asyncio.Future(),  # run forever
            pico_server.serve_forever()
        )
    # async with serve(handler, "0.0.0.0", WS_PORT):
    #     print("==========================================")
    #     print("🚀 WisDrone Gateway Running")
    #     print(f"📡 WebSocket Port: {WS_PORT}")
    #     print(f"📡 TCP (Telemetry) Port: 3002")
    #     print(f"🤖 AI Server: {AI_SERVER_URL}")
    #     print(f"⏱️ AI Send Interval: {AI_SEND_INTERVAL}s")
    #     print("==========================================")
    #     print("")
    #     print("Protocol:")
    #     print("  Drone  → { type: 'DRONE', deviceId: 'xxx' }")
    #     print("  Frontend → { type: 'FRONTEND' }")
    #     print("  Subscribe → { type: 'SUBSCRIBE', deviceId: 'xxx' }")
    #     print("==========================================")
    #     await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGateway stopped.")
