"""
WisDrone Drone Simulator
테스트용 드론 시뮬레이터 - 가상 프레임을 게이트웨이로 전송
"""

import asyncio
import json
import time
import websockets

GATEWAY_URL = "ws://localhost:3001"

async def simulate_drone(device_id=None):
    """드론 시뮬레이터"""
    uri = GATEWAY_URL
    
    try:
        async with websockets.connect(uri) as ws:
            # 1. 드론 핸드셰이크
            handshake = {"type": "DRONE"}
            if device_id:
                handshake["deviceId"] = device_id
            
            await ws.send(json.dumps(handshake))
            
            # 응답 대기
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("type") == "REGISTERED":
                my_id = data.get("deviceId")
                print(f"✅ Registered as: {my_id}")
            else:
                print(f"⚠️ Unexpected response: {data}")
                return
            
            # 2. 가상 프레임 전송
            frame_count = 0
            while True:
                # 가상 프레임 생성 (실제로는 JPEG 바이트)
                fake_frame = f"FRAME_{my_id}_{frame_count}".encode() + b'\x00' * 1000
                
                await ws.send(fake_frame)
                frame_count += 1
                
                if frame_count % 30 == 0:
                    print(f"📤 Sent {frame_count} frames ({my_id})")
                
                await asyncio.sleep(0.033)  # ~30fps
    
    except ConnectionRefusedError:
        print(f"❌ Cannot connect to gateway at {GATEWAY_URL}")
        print("   Make sure gateway is running: ./start_gateway.sh")
    except Exception as e:
        print(f"❌ Error: {e}")


async def simulate_multiple_drones(count=2):
    """여러 드론 동시 시뮬레이션"""
    tasks = []
    for i in range(count):
        device_id = f"drone_sim_{i:02d}"
        tasks.append(simulate_drone(device_id))
    
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import sys
    
    print("==========================================")
    print("🚁 WisDrone Simulator")
    print("==========================================")
    
    if len(sys.argv) > 1:
        # 지정된 수만큼 드론 시뮬레이션
        count = int(sys.argv[1])
        print(f"Starting {count} simulated drones...")
        asyncio.run(simulate_multiple_drones(count))
    else:
        # 단일 드론
        print("Starting single drone simulation...")
        print("Usage: python3 drone_simulator.py [count]")
        print("")
        asyncio.run(simulate_drone())
