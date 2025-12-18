# app/utils/ffmpeg_wrapper.py
"""
Wrapper для FFmpeg с контролируемым логированием.
Позволяет централизованно управлять уровнем логов FFmpeg через ENV.
"""
import os
import subprocess
from typing import List, Optional

# Уровни логирования FFmpeg:
# - "quiet": ничего не выводит
# - "panic": только фатальные ошибки
# - "fatal": критические ошибки
# - "error": все ошибки (по умолчанию в старом коде)
# - "warning": ошибки + предупреждения
# - "info": нормальный режим
FFMPEG_LOG_LEVEL = os.getenv("FFMPEG_LOG_LEVEL", "fatal")
FFPROBE_LOG_LEVEL = os.getenv("FFPROBE_LOG_LEVEL", "fatal")


def get_ffmpeg_base_cmd(threads: int = 1, nice: bool = False) -> List[str]:
    """
    Возвращает базовую команду FFmpeg с настроенным логированием.
    
    Args:
        threads: количество потоков
        nice: использовать nice для снижения приоритета
    """
    cmd = []
    if nice:
        cmd += ["nice", "-n", "10"]
    
    cmd += [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", FFMPEG_LOG_LEVEL,
        "-threads", str(threads),
    ]
    return cmd


def get_ffprobe_base_cmd() -> List[str]:
    """Возвращает базовую команду FFprobe с настроенным логированием."""
    return [
        "ffprobe",
        "-v", FFPROBE_LOG_LEVEL,
    ]


def run_ffmpeg(
    cmd: List[str],
    *,
    timeout: Optional[int] = None,
    check: bool = True,
    capture_output: bool = False,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Запускает FFmpeg команду с логированием и обработкой ошибок.
    
    Args:
        cmd: полная команда FFmpeg
        timeout: таймаут в секундах
        check: бросать исключение при ненулевом коде возврата
        capture_output: захватывать stdout/stderr
        **kwargs: дополнительные аргументы для subprocess.run
    """
    try:
        return subprocess.run(
            cmd,
            timeout=timeout,
            check=check,
            capture_output=capture_output,
            **kwargs
        )
    except subprocess.CalledProcessError as e:
        # Можно добавить логирование или обработку специфичных ошибок
        raise
    except subprocess.TimeoutExpired as e:
        # Таймаут - часто означает зависший процесс
        raise


def run_ffprobe_json(
    path_or_url: str,
    timeout: int = 25,
    show_format: bool = True,
    show_streams: bool = True,
) -> Optional[dict]:
    """
    Запускает ffprobe и возвращает результат в виде JSON.
    
    Args:
        path_or_url: путь к файлу или URL
        timeout: таймаут в секундах
        show_format: включить информацию о формате
        show_streams: включить информацию о потоках
    
    Returns:
        dict с результатами или None при ошибке
    """
    import json
    
    cmd = get_ffprobe_base_cmd() + [
        "-print_format", "json",
    ]
    
    if show_format:
        cmd.append("-show_format")
    if show_streams:
        cmd.append("-show_streams")
    
    cmd.append(path_or_url)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None

