"""
🧪 Gateway Simulator - AI 서버 테스트용

실제 드론/게이트웨이 없이 AI 서버를 테스트합니다.
AI 서버 dataset/images에 있는 이미지를 사용하여
게이트웨이처럼 10초 간격으로 프레임을 전송합니다.

사용법:
    python test_gateway.py
    
    또는 단일 전송:
    python test_gateway.py --once
"""

import os
import sys
import time
import glob
import random
import requests
import argparse

# ==========================================
# Configuration
# ==========================================
AI_SERVER_URL = "http://172.30.1.11:8000/analyze"
TEST_DEVICE_ID = "device_test01"
SEND_INTERVAL = 10.0  # 초

# AI 서버의 dataset 이미지 경로
IMAGE_DIR = "/Users/hyhchan/Desktop/wisdrone-ai-server/dataset/images/train"


def get_test_images():
    """테스트용 이미지 목록 가져오기"""
    patterns = [
        os.path.join(IMAGE_DIR, "*.jpg"),
        os.path.join(IMAGE_DIR, "**/*.jpg"),
    ]
    images = []
    for pattern in patterns:
        images.extend(glob.glob(pattern, recursive=True))
    return images


def send_frame_to_ai(image_path, device_id=TEST_DEVICE_ID):
    """프레임을 AI 서버로 전송 (게이트웨이와 동일한 방식)"""
    try:
        with open(image_path, "rb") as f:
            frame_bytes = f.read()
        
        files = {"file": ("frame.jpg", frame_bytes, "image/jpeg")}
        data = {"device_id": device_id}
        
        print(f"📤 전송 중: {os.path.basename(image_path)} → {device_id}")
        
        response = requests.post(
            AI_SERVER_URL, 
            files=files, 
            data=data, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("data", {})
            
            print(f"✅ 성공!")
            print(f"   👥 인원 수: {data.get('metrics', {}).get('person_count', 'N/A')}")
            print(f"   ⚠️ 위험도: {data.get('risk', {}).get('score', 'N/A')} ({data.get('risk', {}).get('level', 'N/A')})")
            print(f"   📊 밀집도: {data.get('metrics', {}).get('density', 'N/A')}")
            print(f"   🔄 압박: {data.get('metrics', {}).get('pressure', 'N/A')}")
            print()
            return result
        else:
            print(f"❌ 실패: {response.status_code}")
            print(f"   {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 연결 실패: AI 서버가 실행 중인지 확인하세요")
        print(f"   URL: {AI_SERVER_URL}")
        return None
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None


def run_continuous_test(images, interval=SEND_INTERVAL, device_id=TEST_DEVICE_ID):
    """연속 테스트 (게이트웨이처럼 10초 간격 전송)"""
    print("=" * 50)
    print("🚀 Gateway Simulator 시작")
    print(f"📡 AI Server: {AI_SERVER_URL}")
    print(f"🆔 Device ID: {TEST_DEVICE_ID}")
    print(f"⏱️ 전송 간격: {interval}초")
    print(f"🖼️ 테스트 이미지: {len(images)}개")
    print("=" * 50)
    print("종료: Ctrl+C")
    print()
    
    idx = 0
    try:
        while True:
            image = images[idx % len(images)]
            send_frame_to_ai(image, device_id)
            idx += 1
            
            print(f"⏳ {interval}초 후 다음 프레임...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n🛑 테스트 종료")


def run_single_test(images, device_id=TEST_DEVICE_ID):
    """단일 테스트 (한 번만 전송)"""
    print("=" * 50)
    print("🧪 단일 테스트 모드")
    print("=" * 50)
    
    image = random.choice(images)
    result = send_frame_to_ai(image, device_id)
    
    if result:
        print("✅ 테스트 완료!")
    else:
        print("❌ 테스트 실패")


def main():
    parser = argparse.ArgumentParser(description="Gateway Simulator for AI Server Testing")
    parser.add_argument("--once", action="store_true", help="단일 테스트만 실행")
    parser.add_argument("--interval", type=float, default=SEND_INTERVAL, help="전송 간격 (초)")
    parser.add_argument("--device", type=str, default=TEST_DEVICE_ID, help="테스트 디바이스 ID")
    args = parser.parse_args()
    
    device_id = args.device
    
    # 테스트 이미지 가져오기
    images = get_test_images()
    
    if not images:
        print("❌ 테스트 이미지를 찾을 수 없습니다!")
        print(f"   경로: {IMAGE_DIR}")
        sys.exit(1)
    
    if args.once:
        run_single_test(images, device_id)
    else:
        run_continuous_test(images, args.interval, device_id)


if __name__ == "__main__":
    main()
