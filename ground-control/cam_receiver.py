import asyncio
from websockets.server import serve

# Keep track of connected browsers
connected_browsers = set()

async def handler(websocket):
    global connected_browsers
    print(f"Connection opened from: {websocket.remote_address}")
    
    try:
        async for message in websocket:
            # If it's binary data, it's a frame from the ESP32
            if isinstance(message, bytes):
                if connected_browsers:
                    # Send frame to all browsers
                    # Using wait to ensure we don't crash if one browser drops
                    await asyncio.gather(
                        *[browser.send(message) for browser in connected_browsers],
                        return_exceptions=True
                    )
            else:
                # If it's text, check if it's the browser
                if message == "BROWSER":
                    connected_browsers.add(websocket)
                    print(f"Browser added. Total browsers: {len(connected_browsers)}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if websocket in connected_browsers:
            connected_browsers.remove(websocket)
            print("Browser disconnected")

async def main():
    # "0.0.0.0" allows the Jetson to listen on the local network
    async with serve(handler, "0.0.0.0", 3001):
        print("Server started on Jetson Nano at port 3001...")
        await asyncio.Future()  # this keeps the server running forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped.")
