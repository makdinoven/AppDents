import React, { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { resolveHlsUrl } from "../../common/utils/hls.ts"; // см. обновлённый utils/hls.ts

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
  const [useMp4Fallback, setUseMp4Fallback] = useState(!preferHls);
  const [hlsUrl, setHlsUrl] = useState<string | null>(null);

  // 0) внешние провайдеры — сразу iframe

  // 1) Резолвим реальный playlist.m3u8 (с проверкой Content-Type и #EXTM3U)
  useEffect(() => {
    let cancelled = false;

    (async () => {
      if (!preferHls) {
        setHlsUrl(null);
        setUseMp4Fallback(true);
        return;
      }

      setUseMp4Fallback(false); // пробуем HLS снова при смене src
      const url = await resolveHlsUrl(srcMp4);
      if (cancelled) return;

      if (url) {
        setHlsUrl(url);
      } else {
        setHlsUrl(null);
        setUseMp4Fallback(true);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [srcMp4, preferHls]);

  // 2) Инициализация плеера (нативный HLS в Safari / hls.js в остальных)
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // MP4 фолбэк или HLS не найден — ставим обычный mp4-источник
    if (!preferHls || useMp4Fallback || !hlsUrl) {
      video.src = srcMp4;
      return;
    }

    // Safari/iOS: нативная поддержка HLS
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = hlsUrl;
      return;
    }

    // hls.js для остальных браузеров
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
        backBufferLength: 30,
      });

      let manifestOk = false;
      let firstFragLoaded = false;

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(hlsUrl);
      });

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        manifestOk = true;
        if (autoPlay) {
          video.play().catch(() => {});
        }
      });

      hls.on(Hls.Events.FRAG_LOADED, () => {
        firstFragLoaded = true;
      });

      hls.on(Hls.Events.ERROR, (_evt, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              hls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls.recoverMediaError();
              break;
            default:
              hls.destroy();
              setUseMp4Fallback(true);
          }
        }
      });

      hls.attachMedia(video);

      // тайм-ауты защиты: нет манифеста или нет первых сегментов — уходим в mp4
      const tManifest = window.setTimeout(() => {
        if (!manifestOk) {
          try {
            hls.destroy();
          } catch {}
          setUseMp4Fallback(true);
        }
      }, 5000);

      const tFirstFrag = window.setTimeout(() => {
        if (manifestOk && !firstFragLoaded) {
          try {
            hls.destroy();
          } catch {}
          setUseMp4Fallback(true);
        }
      }, 6000);

      return () => {
        window.clearTimeout(tManifest);
        window.clearTimeout(tFirstFrag);
        try {
          hls.destroy();
        } catch {}
      };
    } else {
      setUseMp4Fallback(true);
    }
  }, [hlsUrl, useMp4Fallback, preferHls, srcMp4, autoPlay]);

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
    // если srcMp4 невалидный как URL — тоже iframe (совместимость с существующей логикой)
    // return (
    //   <div className={className}>
    //     <iframe src={srcMp4} width="100%" height="100%" allowFullScreen />
    //   </div>
    // );
  }

  return (
    <video
      ref={videoRef}
      className={className}
      poster={poster}
      controls={controls}
      loop={loop}
      muted={muted}
      playsInline
      preload="metadata" // при желании можно включить
    />
  );
};

export default HlsVideo;
