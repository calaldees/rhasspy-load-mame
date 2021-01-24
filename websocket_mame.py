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
    'cmd_mame': ('groovymame', ),
    'cmd_duck': ('amixer', 'sset', '-c', '1', 'Master'),
    'cmd_mame_exit': ('xdotool', 'key', 'Escape'),
}


class RhasspyIntentProcessor():

    def __init__(self):
        self.process_mame = None

    def close_mame(self):
        if self.process_mame:
            if CONFIG.get('cmd_mame_exit'):  # If we have an explicit command to run to quit MAME, use that in preference - else just kill the process
                self.cmd(CONFIG.get('cmd_mame_exit'))
            else:
                try:
                    self.process_mame.kill()
                    self.process_mame.wait()
                except ProcessLookupError:
                    pass
            self.process_mame = None

    async def mame(self, *args):
        self.close_mame()
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
            self.close_mame()
            #self.reset_resolution()

    async def cmd(self, *args):
        try:
            log.debug(f'cmd: {args}')
            process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
            stdout, _ = await process.communicate()
            return stdout.decode('utf8')
        except Exception as ex:
            return str(ex)

    async def reset_resolution(self):
        # https://mme4crt.alphanudesign.co.uk/forum/showthread.php?tid=5
        process = await asyncio.create_subprocess_shell('''
            output="$(xrandr | grep " connected" | awk '{print$1})" && \
            xrandr --newmode "700x480_59.941002" 13.849698 700 742 801 867 480 490 496 533 interlace -hsync -vsync && \
            xrandr --addmode $output 700x480_59.941002 && \
            xrandr --output $output --mode 700x480_59.941002 
            ''',
            stdout=asyncio.subprocess.PIPE,
            #stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await process.communicate()
        return stdout.decode('utf8')

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
        await self.cmd(*cmd_duck ,'50%' if v else '100%')


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
                print('wakeup')
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
