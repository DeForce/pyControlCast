import asyncio
import functools
import time
import random

from pydub import AudioSegment
from pydub.playback import play


async def test_two():
    time_sl = random.randint(1, 10)
    print(f'From Two, {time_sl}')
    # song = AudioSegment.from_mp3('sounds/da_ladno_g.mp3')
    # play(song - 20)
    await asyncio.sleep(time_sl)
    loop.create_task(test_two())


async def main():
    loop.create_task(test_two())
    loop.create_task(test_two())

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
