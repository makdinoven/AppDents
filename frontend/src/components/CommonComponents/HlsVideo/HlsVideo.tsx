import React, { useEffect, useMemo, useRef, useState } from "react";
import { useHlsSource } from "../../../common/hooks/useHlsSource.ts";
import Hls from "hls.js";

interface HlsVideoProps {
  src: string;
  cdnHost?: string;
  poster?: string;
  autoPlay?: boolean;
  muted?: boolean;
  controls?: boolean;
  className?: string;
}

export const HlsVideo: React.FC<HlsVideoProps> = ({
  src,
  cdnHost,
  poster,
  autoPlay = false,
  muted = false,
  controls = true,
  className,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const source = useHlsSource(src, cdnHost);
  const [hlsInstance, setHlsInstance] = useState<Hls | null>(null);
  const [levels, setLevels] = useState<any>([]);
  const [currentLevel, setCurrentLevel] = useState<number>(-1);

  const canNativeHls = (video: HTMLVideoElement) =>
    video.canPlayType?.("application/vnd.apple.mpegurl") !== "";

  // Инициализация HLS
  useEffect(() => {
    const video = videoRef.current;
    if (!video || source.kind === "loading") return;

    // очистка предыдущего HLS
    hlsInstance?.destroy();
    setLevels([]);
    setCurrentLevel(-1);

    if (source.kind === "hls") {
      if (canNativeHls(video)) {
        video.src = source.url;
      } else if (Hls.isSupported()) {
        const hls = new Hls({ enableWorker: true });
        hls.attachMedia(video);
        hls.loadSource(source.url);

        hls.on(Hls.Events.MANIFEST_PARSED, (_, data) => {
          setLevels(data.levels ?? []);
          setCurrentLevel(-1);
        });

        hls.on(Hls.Events.ERROR, (_, data) => {
          if (data.fatal) {
            hls.destroy();
            setHlsInstance(null);
            video.src = src; // fallback на MP4
          }
        });

        setHlsInstance(hls);
        return () => hls.destroy();
      } else {
        video.src = src; // fallback для старых браузеров
      }
    } else if (source.kind === "mp4") {
      video.src = source.url;
    }
  }, [source, src]);

  useEffect(() => {
    if (hlsInstance) hlsInstance.currentLevel = currentLevel;
  }, [currentLevel, hlsInstance]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = muted;
    if (autoPlay) video.play().catch(() => {});
  }, [autoPlay, muted, source]);

  const levelOptions = useMemo(() => {
    return levels.map((level: any, i: any) => ({
      value: i,
      label: level.height
        ? `${level.height}p`
        : `${Math.round((level.bitrate ?? 0) / 1000)}k`,
    }));
  }, [levels]);

  return (
    <div className={className}>
      <video
        ref={videoRef}
        poster={poster}
        controls={controls}
        playsInline
        preload="metadata"
        crossOrigin="anonymous"
        style={{
          width: "100%",
          height: "auto",
          borderRadius: 12,
          backgroundColor: "black",
        }}
      />
      {levels.length > 0 && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            marginTop: 4,
          }}
        >
          <label style={{ fontSize: 14 }}>Качество:</label>
          <select
            value={currentLevel}
            onChange={(e) => setCurrentLevel(Number(e.target.value))}
            style={{ padding: "4px 8px", borderRadius: 6 }}
          >
            <option value={-1}>Auto</option>
            {levelOptions.map((opt: any) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};
