import asyncio
from websockets.server import serve

connected_browsers = set()

async def handler(websocket):
    global connected_browsers
    print(f"Connection opened from: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            if isinstance(message, bytes):
                # Optimization: Don't wait for browsers. 
                # Fire the send task and move on immediately to get the next frame.
                for browser in list(connected_browsers):
                    try:
                        # This is non-blocking
                        asyncio.create_task(browser.send(message))
                    except:
                        connected_browsers.remove(browser)
            else:
                if message == "BROWSER":
                    connected_browsers.add(websocket)
                    print(f"Browser added. Total: {len(connected_browsers)}")
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        connected_browsers.discard(websocket)

async def main():
    # ping_interval=None and ping_timeout=None disables the heartbeat check 
    # This prevents the "1011 ping timeout" error during high-traffic VGA streams.
    async with serve(handler, "0.0.0.0", 3001, ping_interval=None, ping_timeout=None):
        print("Server started on Jetson Nano. Heartbeat check disabled for stability.")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())