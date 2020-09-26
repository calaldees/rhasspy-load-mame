import asyncio
import websockets  # https://pypi.org/project/websockets/

import json

from pprint import pprint


class RhasspyIntentProcessor():

    def __init__(self):
        self.process = None

    async def mame(self, *args):
        if self.process:
            try:
                self.process.kill()
                self.process.wait()
            except ProcessLookupError:
                pass
            self.process = None
        self.process = await asyncio.create_subprocess_exec(
            'mame',
            *args,
            stdout=asyncio.subprocess.PIPE,
        )
        #stdout, _ = await proc.communicate()
        #print(1)
        #async for line in process.stdout:
        #    print(line)
        #print(2)
        #process.kill()
        #print(3)
        #return await process.wait()

    async def intent(self, data):
        pprint(data)
        if data['intent']['name'] == 'SystemTest':
            await self.mame(
                '-rompath', '/home/pi/rapidseedbox/MAME 0.222 ROMs (merged)/',
                '-window',
                data['slots']['rom']
            )

    async def listen_for_intent(self, uri):
        async with websockets.connect(uri) as websocket:
            while True:
                await self.intent(json.loads(await websocket.recv()))


if __name__ == '__main__':
    rhasspy = RhasspyIntentProcessor()
    asyncio.run(
        rhasspy.listen_for_intent('ws://localhost:12101/api/events/intent')
    )
