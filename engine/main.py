import asyncio

from engine.audio_input_engine import Engine as AudioInputEngine
from engine.stt_engine import Engine as SttEngine
from config.schemas import Parameters


class Engine:
    def __init__(self):
        self._audio_engine = AudioInputEngine()
        self._stt_engine = SttEngine()
        self.queue = asyncio.Queue()
        self._running = False
        self._parameters: Parameters | None = None
        self._grabber_task: asyncio.Task | None = None

    def is_running(self):
        """Статус движка, запущен ли?"""
        return self._running

    def get_parameters(self):
        """Получить текущие параметры"""
        return self._parameters

    async def start(self, parameters: Parameters):
        """Запуск микрофона с распознавателем речи"""
        if not self._running:
            print(f'Запуск движка (подождите)')
            self._running = True
            self._parameters = parameters
            self._audio_engine.start(parameters=self._parameters)
            self._stt_engine.start(parameters=self._parameters)
            self._grabber_task = asyncio.create_task(self._audio_engine.grabber(callback=self.stt_callback))
            print(f'Движок запущен')

    async def stt_callback(self, chunk):
        """Закидывает распознанные фразы в очередь"""
        if self._running:
            res = await self._stt_engine.recognized(chunk=chunk)
            if res.get('type') == 'result':
                await self.queue.put(res)
                # print(res)

    async def stop(self):
        if self._running:
            print(f'Остановка движка (подождите)')
            self._running = False
            if self._grabber_task is not None and not self._grabber_task.done():
                try:
                    await asyncio.wait_for(self._grabber_task, timeout=2)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    self._grabber_task.cancel()
            self._grabber_task = None
            self._audio_engine.stop()
            self._stt_engine.stop()
            self._parameters = None
            self.queue = asyncio.Queue()
            print(f'Движок остановлен')


async def main():
    engine = Engine()
    engine_task = asyncio.create_task(engine.start(parameters=Parameters()))

    async def consumer():
        while engine.is_running():
            try:
                res = await asyncio.wait_for(engine.queue.get(), timeout=0.1)
                print(res)
            except asyncio.TimeoutError:
                pass
            except asyncio.CancelledError:
                pass

    consumer_task = asyncio.create_task(consumer())
    await asyncio.to_thread(lambda: input('... press enter for exit ...\n'))
    await engine.stop()
    await engine_task
    await consumer_task


if __name__ == '__main__':
    asyncio.run(main())
