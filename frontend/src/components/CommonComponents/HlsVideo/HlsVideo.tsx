import React, { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { mp4ToHlsUrl } from "../../../common/utils/hls.ts";

type Props = {
  srcMp4: string;
  poster?: string;
  className?: string;
  autoPlay?: boolean;
  controls?: boolean;
  loop?: boolean;
  muted?: boolean;
  preferHls?: boolean;
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
  muted,
  preferHls = true,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [useMp4Fallback, setUseMp4Fallback] = useState(!preferHls);
  const [resolvedHls, setResolvedHls] = useState<string | null>(null);

  // 2️⃣ Наши mp4 → пробуем HLS
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!preferHls) {
        setResolvedHls(null);
        return;
      }
      const url = await mp4ToHlsUrl(srcMp4);
      if (!cancelled) setResolvedHls(url);
    })();
    return () => {
      cancelled = true;
    };
  }, [srcMp4, preferHls]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (!preferHls || useMp4Fallback || !resolvedHls) {
      video.src = srcMp4;
      return;
    }

    const canNative = video.canPlayType("application/vnd.apple.mpegurl");
    if (canNative) {
      video.src = resolvedHls;
      return;
    }

    if (Hls.isSupported()) {
      const hls = new Hls({ enableWorker: true, lowLatencyMode: false });
      let manifestOk = false;

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls.loadSource(resolvedHls);
      });

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        manifestOk = true;
        if (autoPlay) video.play().catch(() => {});
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

      const t = window.setTimeout(() => {
        if (!manifestOk) {
          try {
            hls.destroy();
          } catch {}
          setUseMp4Fallback(true);
        }
      }, 5000);

      return () => {
        window.clearTimeout(t);
        try {
          hls.destroy();
        } catch {}
      };
    } else {
      setUseMp4Fallback(true);
    }
  }, [resolvedHls, useMp4Fallback, preferHls, srcMp4, autoPlay]);

  try {
    const u = new URL(srcMp4);
    if (externalHosts.some((host) => u.hostname.includes(host))) {
      return (
        <div className={className}>
          <iframe
            src={srcMp4}
            width="100%"
            height="100%"
            frameBorder="0"
            allow="autoplay; fullscreen"
            allowFullScreen
          />
        </div>
      );
    }
  } catch {
    // если невалидный URL — тоже iframe
    return (
      <div className={className}>
        <iframe
          src={srcMp4}
          width="100%"
          height="100%"
          frameBorder="0"
          allow="autoplay; fullscreen"
          allowFullScreen
        />
      </div>
    );
  }

  return (
    <video
      ref={videoRef}
      className={className}
      poster={poster}
      controls={controls}
      autoPlay={autoPlay}
      loop={loop}
      muted={muted}
      playsInline
    />
  );
};

export default HlsVideo;
