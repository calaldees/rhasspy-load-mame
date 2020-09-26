import asyncio
import websockets  # https://pypi.org/project/websockets/

import json

from pprint import pprint

async def hello(uri):
    async with websockets.connect(uri) as websocket:
        response = json.loads(await websocket.recv())
        pprint(response)

asyncio.get_event_loop().run_until_complete(
    hello('ws://localhost:12101/api/events/intent')
)
