import asyncio, sys, subprocess
import warnings, json
from pathlib import Path

"""
Пусковой стартовый скрипт, для сборки зависимостей и скачивания необходимых компонентов.
Важно! Перед запуском должно быть создано виртуальное окружение, и название папки должно быть .venv
"""
steps = 5
lock = asyncio.Lock()


async def installer_log(step: int, description: str):
    """Запись текущей операции в json (для интеграции с лаунчером)"""
    print(f'{step}.{description}')
    async with lock:
        with open(file=Path('installer.json'), mode='w', encoding='utf8') as f:
            f.write(
                json.dumps(
                    {'step': step, 'steps': steps, 'description': description},
                    indent=2,
                    ensure_ascii=False,
                )
            )


async def start():
    await installer_log(step=1, description='установка uv')
    cmd = [sys.executable, '-m', 'pip', 'install', 'uv']
    subprocess.run(cmd, shell=False)

    await installer_log(step=2, description='установка библиотек')
    cmd = [sys.executable, '-m', 'uv', 'sync']
    subprocess.run(cmd, shell=False)

    await installer_log(step=3, description='загрузка моделей')
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

    await installer_log(step=4, description='распаковка моделей')
    import zipfile
    for model in ('vosk-model-small-ru-0.22.zip', 'vosk-model-small-en-us-0.15.zip'):
        zip_path = models_dir / model
        if not zip_path.exists():
            warnings.warn(f'Не удалось скачать модель {model}')
            continue

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(models_dir)
        zip_path.unlink()

    await installer_log(step=5, description='сборка .exe/bin')
    from build import build, parameters
    build(parameters=parameters)


if __name__ == '__main__':
    asyncio.run(start())
