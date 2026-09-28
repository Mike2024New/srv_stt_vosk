import asyncio, sys, subprocess
import warnings

"""
Пусковой стартовый скрипт, для сборки зависимостей и скачивания необходимых компонентов.
Важно! Перед запуском должно быть создано виртуальное окружение, и название папки должно быть .venv
"""


async def start():
    print(f'1. установка uv', flush=True)
    cmd = [sys.executable, '-m', 'pip', 'install', 'uv']
    subprocess.run(cmd, shell=False)
    print(f'#progress 20', flush=True)  # для progress бара

    print(f'2. установка библиотек', flush=True)
    cmd = [sys.executable, '-m', 'uv', 'sync']
    subprocess.run(cmd, shell=False)
    print(f'#progress 40')  # для progress бара

    print(f'3. загрузка моделей', flush=True)
    print('#download start', flush=True)  # сообщить о начале установки для popen парсера
    from infrastructure_http_clients import file_downloader, DownloadFileType
    from config import settings

    models_dir = settings.models_dir_prop  # путь брать из property (дорисовка абсолютного к относительному)

    download_list = [
        DownloadFileType(
            url_list=[
                'https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip',
                'https://github.com/Mike2024New/STT_OFFLINE/releases/download/v1.1.0/vosk-model-small-ru-0.22.zip',
            ],
            target_dir=models_dir,
            filename='vosk-model-small-ru-0.22.zip',
            replace=False,
        ),
        DownloadFileType(
            url_list=[
                'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip',
                'https://github.com/Mike2024New/STT_OFFLINE/releases/download/v1.1.0/vosk-model-small-en-us-0.15.zip',
            ],
            target_dir=models_dir,
            filename='vosk-model-small-en-us-0.15.zip',
            replace=False,
        ),
    ]
    await file_downloader(download_list=download_list, console_progress_bar=True)
    print('#download end', flush=True)  # сообщить о том что загрузка файлов завершена
    print('', flush=True)  # перевод пустой строки
    print(f'#progress 60', flush=True)  # для progress бара

    print(f'4. распаковка моделей', flush=True)
    import zipfile
    for model in ('vosk-model-small-ru-0.22.zip', 'vosk-model-small-en-us-0.15.zip'):
        zip_path = models_dir / model
        if not zip_path.exists():
            warnings.warn(f'Не удалось скачать модель {model}')
            continue

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(models_dir)
        zip_path.unlink()
    print(f'#progress 80', flush=True)  # для progress бара

    print(f'5. сборка .exe/bin', flush=True)
    from build import build, parameters
    build(parameters=parameters)
    print(f'#progress 100', flush=True)  # для progress бара


if __name__ == '__main__':
    asyncio.run(start())
