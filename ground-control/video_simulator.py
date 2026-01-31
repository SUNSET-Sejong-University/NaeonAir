"""
WisDrone Video Simulator
비디오 파일을 읽어 게이트웨이로 전송하는 테스트용 시뮬레이터

사용법:
1. test_videos/ 폴더에 비디오 파일을 넣습니다 (.mp4, .avi, .mov 등)
2. python3 video_simulator.py [비디오파일명]
3. 파일명을 생략하면 test_videos/ 폴더의 첫 번째 비디오를 사용합니다
"""

import asyncio
import json
import time
import os
import sys
import cv2
import websockets
import random
import string
import argparse
from pathlib import Path

# 설정
GATEWAY_URL = "ws://localhost:3001"
VIDEO_FOLDER = Path(__file__).parent / "test_videos"
DEFAULT_FPS = 30  # 비디오 FPS가 없을 경우 기본값


def generate_device_id():
    """Generates a random device ID: device_{random6chars}"""
    chars = string.ascii_lowercase + string.digits
    random_suffix = ''.join(random.choices(chars, k=6))
    return f"device_{random_suffix}"


def get_available_videos():
    """test_videos 폴더의 비디오 파일 목록"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
    videos = []
    
    if VIDEO_FOLDER.exists():
        for f in VIDEO_FOLDER.iterdir():
            if f.suffix.lower() in video_extensions:
                videos.append(f)
    
    return sorted(videos)


def list_videos():
    """사용 가능한 비디오 목록 출력"""
    videos = get_available_videos()
    
    if not videos:
        print(f"\n❌ test_videos/ 폴더에 비디오가 없습니다.")
        print(f"   경로: {VIDEO_FOLDER}")
        print(f"   지원 형식: .mp4, .avi, .mov, .mkv, .webm, .flv")
        return None
    
    print(f"\n📁 사용 가능한 비디오 ({len(videos)}개):")
    for i, v in enumerate(videos, 1):
        size_mb = v.stat().st_size / (1024 * 1024)
        print(f"   {i}. {v.name} ({size_mb:.1f}MB)")
    
    return videos


async def simulate_from_video(video_path, device_id=None, loop_video=True):
    """비디오 파일을 읽어 게이트웨이로 전송"""
    
    if not device_id:
        device_id = generate_device_id()

    # OpenCV로 비디오 열기
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        print(f"❌ 비디오를 열 수 없습니다: {video_path}")
        return
    
    # 비디오 정보
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or DEFAULT_FPS
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps
    
    print(f"\n📹 비디오 정보:")
    print(f"   파일: {video_path.name}")
    print(f"   해상도: {width}x{height}")
    print(f"   FPS: {fps:.1f}")
    print(f"   총 프레임: {total_frames}")
    print(f"   재생시간: {duration:.1f}초")
    print(f"   루프: {'활성화' if loop_video else '비활성화'}")
    print(f"   Device ID: {device_id}")
    
    frame_interval = 1.0 / fps
    
    try:
        async with websockets.connect(GATEWAY_URL) as ws:
            # 1. 드론 핸드셰이크
            handshake = {
                "type": "DRONE",
                "deviceId": device_id
            }
            
            await ws.send(json.dumps(handshake))
            
            # 응답 대기
            response = await ws.recv()
            data = json.loads(response)
            
            if data.get("type") == "REGISTERED":
                registered_id = data.get("deviceId")
                # 게이트웨이가 할당해준 ID가 다를 수도 있지만, 요청한 ID가 우선되어야 함
                print(f"\n✅ 게이트웨이에 등록됨: {registered_id}")
                if registered_id != device_id:
                     print(f"⚠️ 요청한 ID({device_id})와 등록된 ID({registered_id})가 다릅니다.")
                     # 실제 전송에는 등록된 ID 사용
                     my_id = registered_id
                else:
                    my_id = device_id
            else:
                print(f"⚠️ 예상치 못한 응답: {data}")
                return
            
            # 2. 프레임 전송 루프
            frame_count = 0
            loop_count = 0
            start_time = time.time()
            
            print(f"🎬 스트리밍 시작...")
            print(f"   Ctrl+C로 중지")
            print("")
            
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    if loop_video:
                        # 비디오 처음으로
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        loop_count += 1
                        print(f"🔄 루프 #{loop_count}")
                        continue
                    else:
                        print(f"\n✅ 비디오 끝. 총 {frame_count}개 프레임 전송됨.")
                        break
                
                # JPEG로 인코딩
                _, jpeg_bytes = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                
                # 게이트웨이로 전송
                await ws.send(jpeg_bytes.tobytes())
                frame_count += 1
                
                # 진행상황 출력 (1초마다)
                if frame_count % int(fps) == 0:
                    elapsed = time.time() - start_time
                    actual_fps = frame_count / elapsed
                    progress = (cap.get(cv2.CAP_PROP_POS_FRAMES) / total_frames) * 100
                    print(f"📤 {frame_count}프레임 | {progress:.1f}% | 실제 FPS: {actual_fps:.1f}")
                
                # FPS 유지를 위한 대기
                await asyncio.sleep(frame_interval)
    
    except ConnectionRefusedError:
        print(f"\n❌ 게이트웨이에 연결할 수 없습니다: {GATEWAY_URL}")
        print(f"   게이트웨이를 먼저 시작하세요: ./start_gateway.sh")
    except KeyboardInterrupt:
        print(f"\n⏹️ 사용자에 의해 중지됨. 총 {frame_count}개 프레임 전송됨.")
    except Exception as e:
        print(f"❌ 오류: {e}")
    finally:
        cap.release()


async def simulate_multiple_videos(video_paths, loop_video=True):
    """여러 비디오를 동시에 시뮬레이션 (각각 다른 드론으로)"""
    tasks = []
    for i, video_path in enumerate(video_paths):
        # 다중 비디오 시뮬레이션 시 랜덤 ID 각각 생성
        device_id = generate_device_id()
        print(f"Preparing video {i}: {video_path.name} as {device_id}")
        tasks.append(simulate_from_video(video_path, device_id, loop_video))
    
    await asyncio.gather(*tasks)


def main():
    print("==========================================")
    print("🎥 WisDrone Video Simulator")
    print("==========================================")
    
    # test_videos 폴더 확인/생성
    VIDEO_FOLDER.mkdir(exist_ok=True)
    
    videos = get_available_videos()

    parser = argparse.ArgumentParser(description="WisDrone Video Simulator")
    parser.add_argument("video_file", nargs="?", help="Video file name or path")
    parser.add_argument("--device-id", help="Specify device ID (e.g., device_abc123)")
    parser.add_argument("--all", action="store_true", help="Play all available videos simultaneously")
    parser.add_argument("--list", "-l", action="store_true", help="List available video files")
    parser.add_argument("--no-loop", action="store_true", help="Do not loop video")

    args = parser.parse_args()

    if args.list:
        list_videos()
        return

    if args.all:
        if not videos:
            list_videos()
            return
        print(f"\n🚁 {len(videos)}개 비디오 동시 스트리밍...")
        asyncio.run(simulate_multiple_videos(videos, loop_video=not args.no_loop))
        return

    # 단일 비디오 처리
    video_path = None
    if args.video_file:
        if os.path.exists(args.video_file):
            video_path = Path(args.video_file)
        else:
            video_path = VIDEO_FOLDER / args.video_file
        
        if not video_path.exists():
            print(f"\n❌ 파일을 찾을 수 없습니다: {args.video_file}")
            list_videos()
            return
    else:
        # 인자 없음 - 첫 번째 비디오 사용
        if not videos:
            list_videos()
            print(f"\n💡 비디오 파일을 {VIDEO_FOLDER}/ 폴더에 넣어주세요!")
            return
        video_path = videos[0]
        print(f"\n🎬 기본 비디오 사용: {video_path.name}")

    asyncio.run(simulate_from_video(video_path, device_id=args.device_id, loop_video=not args.no_loop))


if __name__ == "__main__":
    main()
