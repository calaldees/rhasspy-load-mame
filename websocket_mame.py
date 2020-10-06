import asyncio
import json
import os.path
import re
from pprint import pprint

import websockets  # https://pypi.org/project/websockets/

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
        #print(args)
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
        await self.volume_duck(False)
        pprint(data)
        if data['intent']['name'] == 'Mame':
            await self.mame(
                '-rompath', '/home/pi/rapidseedbox/MAME 0.224 ROMs (merged)/;/home/pi/rapidseedbox/MAME 0.224 Software List ROMs (merged)/',
                '-window',
                '-skip_gameinfo',
                *data['slots']['rom'].split('/'),
            )

    async def cmd(self, *args):
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        return stdout.decode('utf8')

    async def volume_duck(self, v):
        """
        amixer scontrols
        Simple mixer control 'Bose QuietComfort 35 - A2DP',0
        Simple mixer control 'Bose QuietComfort 35 - SCO',0

        amixer sset 'Bose QuietComfort 35 - A2DP' 100%
        """
        match = re.search(r"'(.*)'", await self.cmd('amixer', 'scontrols'))
        if not match:
            log.debug('Unable to list ALSA devices?')
            return
        log.info(f'duck {v}')
        await self.cmd('amixer', 'sset', match.group(1), '50%' if v else '100%')


    async def listen_for_intent(self, uri):
        async with websockets.connect(uri) as websocket:
            log.info(uri)
            while True:
                await self.intent(json.loads(await websocket.recv()))

    async def listen_for_wake(self, uri):
        async with websockets.connect(uri) as websocket:
            log.info(uri)
            while True:
                await websocket.recv()
                await self.volume_duck(True)

    async def run(self, url):
        task1 = asyncio.create_task(self.listen_for_intent(
            os.path.join(url, 'api/events/intent')
        ))
        task2 = asyncio.create_task(self.listen_for_wake(
            os.path.join(url, 'api/events/wake')
        ))
        await task1
        await task2


if __name__ == '__main__':
    rhasspy = RhasspyIntentProcessor()
    asyncio.run(
        rhasspy.run('ws://localhost:12101/')
        #await asyncio.gather(
        #    rhasspy.listen_for_intent('ws://localhost:12101/api/events/intent'),
        #    rhasspy.listen_for_intent('ws://localhost:12101/api/events/wake'),
        #)
    )
