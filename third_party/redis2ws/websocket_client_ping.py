"""
Simple websocket client to conenct to the server
"""

import asyncio
import time
import websockets

async def hello():
    uri = "ws://127.0.0.1:8080/ws"
    async with websockets.connect(uri) as websocket:

        message = input("Enter your message: ")
        start_time = time.time()
        duration = 10
        processed = 0
        while True and time.time() - start_time < duration:
            await websocket.send(message)
            response = await websocket.recv()
            processed += 1
            print(response)

        print(f"Processed {processed} messages in {duration} seconds")

asyncio.get_event_loop().run_until_complete(hello())


