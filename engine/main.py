import asyncio, numpy
from engine.audio_input_engine import Engine as AudioInputEngine
from engine.stt_engine import Engine as SttEngine
from config.schemas import Parameters
from queue import Queue, Empty


class Engine:
    def __init__(self):
        self._audio_engine = AudioInputEngine()
        self._stt_engine = SttEngine()
        self.queue = Queue()
        self._running = False
        self._parameters: Parameters | None = None

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
            self._stt_engine.start(parameters=self._parameters)
            self._audio_engine.start(
                parameters=self._parameters,
                callback=self.stt_callback,
            )

            print(f'Движок запущен')

    def stt_callback(self, indata, _frames, _time, _status):
        """Закидывает распознанные фразы в очередь"""
        if self._running:
            indata_int16 = (indata * 32768).astype(numpy.int16)
            chunk_bytes = indata_int16.tobytes()
            res = self._stt_engine.recognized(chunk=chunk_bytes)
            if res.get('type') == 'result':
                self.queue.put(res)

    async def stop(self):
        if self._running:
            print(f'Остановка движка (подождите)')
            self._running = False
            self._audio_engine.stop()
            self._stt_engine.stop()
            self._parameters = None
            self.queue = Queue()
            print(f'Движок остановлен')


async def main():
    engine = Engine()
    engine_task = asyncio.create_task(engine.start(parameters=Parameters()))

    async def consumer():
        while engine.is_running():
            try:
                res = engine.queue.get_nowait()
                print(res)
            except Empty:
                await asyncio.sleep(0.05)

    consumer_task = asyncio.create_task(consumer())
    await asyncio.to_thread(lambda: input('... press enter for exit ...\n'))
    await engine.stop()
    await engine_task
    await consumer_task


if __name__ == '__main__':
    asyncio.run(main())
