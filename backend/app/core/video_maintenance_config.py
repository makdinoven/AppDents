from __future__ import annotations

"""
Кодовая конфигурация video_maintenance (без ENV для порогов/лимитов).

Идея: вы сначала прогоняете 2–3 видео вручную (через API),
потом включаете расписание в celery beat.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoMaintenanceConfig:
    # Сколько mp4 обрабатываем за один тик периодической таски
    batch_size: int = 3

    # Листинг S3: сколько ключей просить за один запрос list_objects_v2
    list_page_size: int = 250

    # Очередь Celery для этой задачи
    queue: str = "special"

    # По умолчанию периодический тик удаляет старый key после успешного завершения
    delete_old_key_by_default: bool = True

    # Режимы ffmpeg/ffprobe
    ffmpeg_timeout_sec: int = 60 * 30  # 30 минут

    # Таргет для совместимости
    target_video_codec: str = "libx264"
    target_audio_codec: str = "aac"
    target_pixel_format: str = "yuv420p"
    h264_profile: str = "main"
    h264_level: str = "4.1"
    video_preset: str = "veryfast"
    video_crf: int = 23

    audio_bitrate: str = "160k"
    audio_channels: int = 2
    audio_rate_hz: int = 48000

    # HLS: если сегментов слишком много, проверяем только первые N (для скорости)
    hls_segment_head_limit: int = 30

    # Минимальный размер сегмента в байтах (грубая защита от «пустышек»)
    hls_min_segment_size_bytes: int = 512

    # ACL: если HLS существует, но файлы приватные — браузер не сможет их скачать.
    # Чиним ACL на public-read для master/variant и нескольких первых сегментов.
    hls_fix_acl_public_read: bool = True
    hls_fix_acl_max_files: int = 50


VIDEO_MAINTENANCE = VideoMaintenanceConfig()


