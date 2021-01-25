import asyncio
import json
import os
import re
import pprint

import websockets  # https://pypi.org/project/websockets/

import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


CONFIG_PI = {
    'cmd_mame': (
        'mame',
        '-rompath', '/home/pi/rapidseedbox/MAME 0.227 ROMs (merged)/;/home/pi/rapidseedbox/MAME 0.227 Software List ROMs (merged)/',
        '-window',
        '-skip_gameinfo',
    ),
}

CONFIG = {
    'wakeword': 'porcupine',
    'cmd_mame': ('groovymame', ),
    'cmd_duck': ('amixer', 'sset', '-c', '1', 'Master'),
    'duck_vol': '80%',
    'cmd_reset_resolution': ('xrandr', '--output', 'VGA-0', '--mode', '640x480i')  # 640x480i setup already in GroovyArcade
}


class RhasspyIntentProcessor():

    def __init__(self):
        self.process_mame = None

    async def close_mame(self):
        if self.process_mame:
            try:
                self.process_mame.kill()
                self.process_mame.wait()
            except ProcessLookupError:
                pass
            self.process_mame = None

    async def mame(self, *args):
        await self.close_mame()
        self.process_mame = await asyncio.create_subprocess_exec(*CONFIG['cmd_mame'], *args, stdout=asyncio.subprocess.PIPE)

    async def search(self, *args):
        return await self.cmd(
            'docker', 'exec',
            '--workdir', '/_profiles/en/slots/mame/',
            'rhasspy',
            'grep', '-r', ' '.join(args),
        )

    async def intent(self, data):
        await self.volume_duck(False)
        log.debug(pprint.pformat(data))
        os.system('cls||clear')  # clear terminal screen
        print(' '.join(data['raw_tokens']))

        intent = data['intent']['name']
        if intent == 'MameSearch':
            print()
            print(await self.search(*data['raw_tokens'][1:]))
        if intent == 'MameLoad':
            print(data['slots']['rom'])
            await self.mame(*data['slots']['rom'].split('/'))
        if intent == 'MameExit':
            await self.close_mame()
            await self.reset_resolution()

    async def cmd(self, *args):
        try:
            log.debug(f'cmd: {args}')
            process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
            stdout, _ = await process.communicate()
            return stdout.decode('utf8')
        except Exception as ex:
            return str(ex)

    async def reset_resolution(self):
        if CONFIG.get['cmd_reset_resolution']:
            return await self.cmd(CONFIG.get['cmd_reset_resolution'])

    async def volume_duck(self, v):
        """
        amixer scontrols
        Simple mixer control 'Bose QuietComfort 35 - A2DP',0
        Simple mixer control 'Bose QuietComfort 35 - SCO',0

        amixer sset 'Bose QuietComfort 35 - A2DP' 100%

        TODO: This is compicated for multiple audio devices - I need a good way of findind the default playback master volume
        For now we can explicitly provide a duck command for the specific machine
        """
        cmd_duck = CONFIG.get('cmd_duck')
        if not cmd_duck:
            match = re.search(r"'(.*)'", await self.cmd('amixer', 'scontrols'))
            if not match:
                log.debug('Unable to list ALSA devices?')
                return
            cmd_duck = ('amixer', 'sset', match.group(1))
        log.debug(f'duck {v}')
        await self.cmd(*cmd_duck , CONFIG.get('duck_vol', '50%') if v else '100%')


    async def listen_for_intent(self, uri):
        async with websockets.connect(uri) as websocket:
            log.info(uri)
            while True:
                await self.intent(json.loads(await websocket.recv()))

    async def listen_for_wake(self, uri):
        print(f"Wake word: {CONFIG.get('wakeword')}")
        async with websockets.connect(uri) as websocket:
            log.info(uri)
            while True:
                await websocket.recv()
                print('Listening: say "load" or "search"')
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
    asyncio.run(rhasspy.run('ws://localhost:12101/'))
