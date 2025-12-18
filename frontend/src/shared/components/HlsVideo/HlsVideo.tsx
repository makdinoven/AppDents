import React, { useEffect, useRef, useState, useCallback } from "react";
import Hls, { ErrorData } from "hls.js";
import { resolveHlsUrl } from "../../common/utils/hls.ts";

type Props = {
  srcMp4: string;
  poster?: string;
  className?: string;
  autoPlay?: boolean;
  controls?: boolean;
  loop?: boolean;
  muted?: boolean;
  preferHls?: boolean; // по умолчанию true
};

const externalHosts = [
  "play.boomstream.com",
  "player.vimeo.com",
  "vimeo.com",
  "kinescope.io",
  "vk.com",
];

// АГРЕССИВНАЯ конфигурация - при ошибке БЫСТРО fallback на MP4
const HLS_CONFIG: Partial<Hls["config"]> = {
  enableWorker: true,
  lowLatencyMode: false,
  
  // Буферизация
  backBufferLength: 30,
  maxBufferLength: 30,
  maxMaxBufferLength: 60,
  maxBufferHole: 0.5,
  
  // БЫСТРЫЕ таймауты - не ждём долго
  manifestLoadingTimeOut: 8000,       // 8s
  manifestLoadingMaxRetry: 1,
  manifestLoadingRetryDelay: 500,
  
  levelLoadingTimeOut: 8000,          // 8s
  levelLoadingMaxRetry: 1,
  levelLoadingRetryDelay: 500,
  
  // Фрагменты - короткие таймауты, мало retry
  fragLoadingTimeOut: 10000,          // 10s - НЕ ЖДЁМ 40 секунд!
  fragLoadingMaxRetry: 1,             // 1 retry и fallback
  fragLoadingRetryDelay: 500,
  
  startFragPrefetch: true,
  testBandwidth: false,
  startLevel: -1,
};

// Таймаут для нативного HLS (секунды)
const NATIVE_HLS_PLAYBACK_TIMEOUT = 8; // 8 секунд на начало воспроизведения

const HlsVideo: React.FC<Props> = ({
  srcMp4,
  poster,
  className,
  autoPlay,
  controls = true,
  loop,
  muted = true,
  preferHls = true,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [useMp4Fallback, setUseMp4Fallback] = useState(!preferHls);
  const [hlsUrl, setHlsUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Ref для таймеров чтобы очищать их
  const fallbackTimerRef = useRef<number | null>(null);
  const playbackStartedRef = useRef(false);

  // Очистка таймеров
  const clearFallbackTimer = useCallback(() => {
    if (fallbackTimerRef.current) {
      window.clearTimeout(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
  }, []);

  // БЫСТРЫЙ fallback на MP4
  const fallbackToMp4 = useCallback(() => {
    console.log("[HLS] FAST fallback to MP4:", srcMp4);
    
    clearFallbackTimer();
    playbackStartedRef.current = false;
    
    // Уничтожаем HLS instance если есть
    if (hlsRef.current) {
      try {
        hlsRef.current.destroy();
      } catch (e) {
        console.warn("[HLS] Error destroying:", e);
      }
      hlsRef.current = null;
    }
    
    setUseMp4Fallback(true);
    setIsLoading(false);
    
    // Устанавливаем MP4 напрямую
    if (videoRef.current) {
      videoRef.current.src = srcMp4;
      videoRef.current.load();
    }
  }, [srcMp4, clearFallbackTimer]);

  // 1) Резолвим реальный playlist.m3u8
  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    playbackStartedRef.current = false;

    (async () => {
      if (!preferHls) {
        setHlsUrl(null);
        setUseMp4Fallback(true);
        setIsLoading(false);
        return;
      }

      setUseMp4Fallback(false);
      
      try {
        const url = await resolveHlsUrl(srcMp4);
        if (cancelled) return;

        if (url) {
          setHlsUrl(url);
        } else {
          setHlsUrl(null);
          setUseMp4Fallback(true);
        }
      } catch (e) {
        console.warn("[HLS] Error resolving HLS URL:", e);
        if (!cancelled) {
          setHlsUrl(null);
          setUseMp4Fallback(true);
        }
      }
      
      if (!cancelled) {
        setIsLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [srcMp4, preferHls]);

  // 2) Инициализация плеера
  useEffect(() => {
    const video = videoRef.current;
    if (!video || isLoading) return;

    clearFallbackTimer();
    playbackStartedRef.current = false;

    // Очищаем предыдущий hls instance
    if (hlsRef.current) {
      try {
        hlsRef.current.destroy();
      } catch {}
      hlsRef.current = null;
    }

    // MP4 фолбэк или HLS не найден
    if (!preferHls || useMp4Fallback || !hlsUrl) {
      console.log("[Video] Using MP4 source:", srcMp4);
      video.src = srcMp4;
      video.load();
      return;
    }

    // Safari/iOS: нативная поддержка HLS
    // ВАЖНО: добавляем таймаут на начало воспроизведения!
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      console.log("[Video] Native HLS:", hlsUrl);
      video.src = hlsUrl;
      video.load();
      
      // Таймаут для нативного HLS - если не начало играть за N секунд - fallback
      fallbackTimerRef.current = window.setTimeout(() => {
        if (!playbackStartedRef.current) {
          console.error(`[HLS] Native HLS timeout - no playback in ${NATIVE_HLS_PLAYBACK_TIMEOUT}s, falling back to MP4`);
          fallbackToMp4();
        }
      }, NATIVE_HLS_PLAYBACK_TIMEOUT * 1000);
      
      return;
    }

    // hls.js для остальных браузеров
    if (Hls.isSupported()) {
      console.log("[HLS] Initializing hls.js for:", hlsUrl);
      const hls = new Hls(HLS_CONFIG);
      hlsRef.current = hls;

      let firstFragLoaded = false;
      let destroyed = false;

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        if (!destroyed) {
          hls.loadSource(hlsUrl);
        }
      });

      hls.on(Hls.Events.MANIFEST_PARSED, (_evt, data) => {
        console.log("[HLS] Manifest loaded:", data.levels.length, "quality levels");
        if (autoPlay && !destroyed) {
          video.play().catch(() => {});
        }
      });

      hls.on(Hls.Events.FRAG_LOADED, () => {
        if (!firstFragLoaded) {
          firstFragLoaded = true;
          playbackStartedRef.current = true;
          clearFallbackTimer();
          console.log("[HLS] First fragment loaded");
        }
      });

      // При ЛЮБОЙ фатальной ошибке - СРАЗУ fallback
      hls.on(Hls.Events.ERROR, (_evt, data: ErrorData) => {
        if (destroyed) return;
        
        const { type, details, fatal } = data;
        console.warn("[HLS] Error:", type, details, "fatal:", fatal);

        if (fatal) {
          // СРАЗУ fallback - не тратим время на recovery
          console.error("[HLS] Fatal error - immediate fallback to MP4");
          destroyed = true;
          fallbackToMp4();
        }
      });

      hls.attachMedia(video);

      // Быстрый таймаут - 8 секунд
      fallbackTimerRef.current = window.setTimeout(() => {
        if (!destroyed && !firstFragLoaded) {
          console.error("[HLS] Timeout - no fragment in 8s, falling back to MP4");
          destroyed = true;
          fallbackToMp4();
        }
      }, 8000);

      return () => {
        destroyed = true;
        clearFallbackTimer();
        try {
          hls.destroy();
        } catch {}
        hlsRef.current = null;
      };
    } else {
      console.log("[HLS] hls.js not supported, using MP4");
      fallbackToMp4();
    }
  }, [hlsUrl, useMp4Fallback, preferHls, srcMp4, autoPlay, isLoading, fallbackToMp4, clearFallbackTimer]);

  // Cleanup при unmount
  useEffect(() => {
    return () => {
      clearFallbackTimer();
    };
  }, [clearFallbackTimer]);

  // Проверка на внешние хосты
  try {
    const u = new URL(srcMp4);
    if (externalHosts.some((host) => u.hostname.includes(host))) {
      return (
        <div className={className}>
          <iframe src={srcMp4} width="100%" height="100%" allowFullScreen />
        </div>
      );
    }
  } catch {
    // невалидный URL - продолжаем с video
  }

  // Обработчик ошибок - МГНОВЕННЫЙ fallback
  const handleVideoError = useCallback((e: React.SyntheticEvent<HTMLVideoElement>) => {
    const video = e.currentTarget;
    const currentSrc = video.src || "";
    const error = video.error;
    
    console.warn("[Video] Error:", error?.code, error?.message, "src:", currentSrc.slice(-50));
    
    // Если ошибка на HLS - СРАЗУ переключаемся на MP4
    if (!useMp4Fallback && currentSrc.includes(".m3u8")) {
      console.log("[Video] HLS error - immediate fallback to MP4");
      fallbackToMp4();
      return;
    }
    
    // Ошибка на MP4 - ничего не делаем, пусть браузер пробует
    console.log("[Video] MP4 error - letting browser handle");
  }, [useMp4Fallback, fallbackToMp4]);

  // Обработчик начала воспроизведения - отменяем таймаут
  const handlePlaying = useCallback(() => {
    console.log("[Video] Playback started");
    playbackStartedRef.current = true;
    clearFallbackTimer();
  }, [clearFallbackTimer]);

  // Обработчик timeupdate - тоже означает что воспроизведение идёт
  const handleTimeUpdate = useCallback(() => {
    if (!playbackStartedRef.current) {
      playbackStartedRef.current = true;
      clearFallbackTimer();
    }
  }, [clearFallbackTimer]);

  // Обработчик stalled - быстрый fallback для HLS
  const handleStalled = useCallback(() => {
    console.warn("[Video] Playback stalled");
    
    // Если HLS и ещё не началось воспроизведение - fallback
    if (!useMp4Fallback && !playbackStartedRef.current) {
      console.log("[Video] HLS stalled before playback - fallback to MP4");
      fallbackToMp4();
    }
  }, [useMp4Fallback, fallbackToMp4]);

  const handleWaiting = useCallback(() => {
    console.log("[Video] Waiting for data...");
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    console.log("[Video] Metadata loaded");
  }, []);

  const handleCanPlay = useCallback(() => {
    console.log("[Video] Can play");
  }, []);

  return (
    <video
      ref={videoRef}
      className={className}
      poster={poster}
      controls={controls}
      loop={loop}
      muted={muted}
      playsInline
      preload="metadata"
      onError={handleVideoError}
      onPlaying={handlePlaying}
      onTimeUpdate={handleTimeUpdate}
      onLoadedMetadata={handleLoadedMetadata}
      onStalled={handleStalled}
      onWaiting={handleWaiting}
      onCanPlay={handleCanPlay}
    />
  );
};

export default HlsVideo;
