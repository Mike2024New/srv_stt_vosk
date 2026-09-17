import asyncio
import soundcard as sc
import numpy as np
from typing import Callable, Awaitable
from config.schemas import Parameters

import platform

if platform.system() == 'Windows':
    import warnings
    from soundcard.mediafoundation import SoundcardRuntimeWarning

    # подавление логов soundcard (иногда он выводит лишние предупреждения)
    warnings.filterwarnings('ignore', category=SoundcardRuntimeWarning)
else:
    # на Linux soundcard работает через pulseaudio
    pass

"""
Упрощенный класс аудиозахвата микрофона
"""


class Engine:
    def __init__(self):
        self._audio_input = None
        self._event = asyncio.Event()
        self._parameters: Parameters | None = None

    def is_running(self):
        """Статус движка, запущен ли?"""
        return self._audio_input is not None

    def get_parameters(self):
        """Получить текущие параметры"""
        return self._parameters

    def start(self, parameters: Parameters):
        """Загрузка модели (тяжелых ресурсов)"""
        self._parameters = parameters
        self._audio_input = sc.default_microphone()

    async def grabber(self, callback: Callable[[bytes], Awaitable[None]]):
        """Запуск микрофона. Получает сырой pcm переводит его в байты и применяет к нему callback"""
        self._event.clear()
        with self._audio_input.recorder(samplerate=self._parameters.samplerate, channels=1) as input_recorder:
            while not self._event.is_set():
                chunk = input_recorder.record(numframes=self._parameters.blocksize)
                chunk_int16 = (chunk * 32767).astype(np.int16)
                chunk_bytes = chunk_int16.tobytes()
                await callback(chunk_bytes)
                await asyncio.sleep(0)

    def stop(self):
        """Высвобождение ресурсов"""
        self._event.set()
        if self._audio_input is not None:
            del self._audio_input
            self._audio_input = None
        self._parameters = None


async def main():
    engine = Engine()
    engine.start(parameters=Parameters())

    async def callback(chunk):
        print(chunk)

    grabber_task = asyncio.create_task(engine.grabber(callback=callback))
    await asyncio.to_thread(lambda: input())
    engine.stop()
    await grabber_task


if __name__ == '__main__':
    asyncio.run(main())
