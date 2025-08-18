import { useEffect, useState } from "react";
import { buildHlsUrl } from "../utils/buildHlsUrl";

export type SourceInfo =
  | { kind: "hls"; url: string }
  | { kind: "mp4"; url: string }
  | { kind: "loading" };

export function useHlsSource(originalUrl: string, cdnHost?: string) {
  const [source, setSource] = useState<SourceInfo>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    const checkHls = async () => {
      const hlsUrl = buildHlsUrl(originalUrl, cdnHost);
      if (hlsUrl) {
        try {
          const res = await fetch(hlsUrl, { method: "HEAD", mode: "cors" });
          if (!cancelled && res.ok) {
            setSource({ kind: "hls", url: hlsUrl });
            return;
          }
        } catch {}
      }

      if (!cancelled) setSource({ kind: "mp4", url: originalUrl });
    };

    checkHls();

    return () => {
      cancelled = true;
    };
  }, [originalUrl, cdnHost]);

  return source;
}
