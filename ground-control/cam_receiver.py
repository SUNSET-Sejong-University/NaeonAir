import asyncio
import json
import time
import requests  # HTTP requests (AI Server upload / AI 서버 업로드용)
from websockets.server import serve
from functools import partial

# ==========================================
# Configuration / 설정
# ==========================================
# 🔴 [중요] 맥북 IP로 변경하세요!
AI_SERVER_URL = "http://192.168.0.XX:8000/analyze"
SNAPSHOT_INTERVAL = 1.0  # Upload every 1 second / 1초마다 업로드

# Global variables / 전역 변수
connected_browsers = set()
# ✅ 프론트엔드에서 받은 제어값을 저장하는 변수
control_signals = {"throttle": 1000, "pitch": 1000}
last_upload_time = 0  # To track upload timing / 업로드 시간 체크용


# ==========================================
# Helper Function: Upload Image (Run in Thread)
# 헬퍼 함수: 이미지 업로드 (쓰레드에서 실행됨 - 영상 끊김 방지)
# ==========================================
def upload_to_ai(image_bytes):
    try:
        files = {"file": ("snapshot.jpg", image_bytes, "image/jpeg")}
        # Timeout is crucial / 타임아웃 설정 (서버 느릴 때 멈춤 방지)
        response = requests.post(AI_SERVER_URL, files=files, timeout=0.5)
        # print(f"📸 Snapshot uploaded: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Upload Failed: {e}")


# ==========================================
# WebSocket Handler
# 웹소켓 핸들러
# ==========================================
async def handler(websocket):
    global connected_browsers, control_signals, last_upload_time
    print(f"Connection opened from: {websocket.remote_address}")

    loop = asyncio.get_running_loop()

    try:
        async for message in websocket:
            # -------------------------------------------------
            # Case 1: Binary Data (Video Frame from Drone)
            # 케이스 1: 바이너리 데이터 (드론 영상)
            # -------------------------------------------------
            if isinstance(message, bytes):
                current_time = time.time()

                # A. Send to Browsers (Real-time Stream)
                # A. 브라우저로 영상 전송 (스트리밍)
                if connected_browsers:
                    await asyncio.gather(
                        *[browser.send(message) for browser in connected_browsers],
                        return_exceptions=True,
                    )

                # B. Send to AI Server (Every 1 second)
                # B. AI 서버로 스냅샷 전송 (1초 간격)
                if current_time - last_upload_time >= SNAPSHOT_INTERVAL:
                    last_upload_time = current_time
                    # Run upload in thread / 별도 쓰레드에서 업로드 실행
                    loop.run_in_executor(None, partial(upload_to_ai, message))

            # -------------------------------------------------
            # Case 2: Text Data (Control Signal from Frontend)
            # 케이스 2: 텍스트 데이터 (프론트엔드 제어 신호)
            # -------------------------------------------------
            else:
                # Browser Handshake / 브라우저 연결 확인
                if message == "BROWSER":
                    connected_browsers.add(websocket)
                    print(f"✅ Browser added. Total: {len(connected_browsers)}")

                # ✅ [핵심] Receive Control Data from Frontend
                # ✅ 프론트엔드에서 보낸 제어값(JSON) 수신부
                elif message.startswith("{"):
                    try:
                        data = json.loads(message)
                        if "throttle" in data and "pitch" in data:
                            # Update global variable / 전역 변수 업데이트
                            control_signals["throttle"] = data["throttle"]
                            control_signals["pitch"] = data["pitch"]

                            # Log for debugging / 확인용 로그 출력
                            print(
                                f"🎮 CMD Recv: T={data['throttle']}, P={data['pitch']}"
                            )

                            # [Future Work] Send MAVLink to FC here
                            # [추후 작업] 여기서 시리얼 통신으로 FC에 명령 전달

                    except json.JSONDecodeError:
                        print("⚠️ Invalid JSON")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if websocket in connected_browsers:
            connected_browsers.remove(websocket)
            print("Browser disconnected")


# ==========================================
# Main Server Loop
# 메인 서버 루프
# ==========================================
async def main():
    async with serve(handler, "0.0.0.0", 3001):
        print("========================================")
        print("🚁 Jetson Gateway Running (Port 3001)")
        print(f"📡 AI Server Target: {AI_SERVER_URL}")
        print("🎮 Waiting for Control Signals...")
        print("========================================")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")
