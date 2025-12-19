import React, { useEffect, useRef, useState, useCallback } from "react";
import Hls, { ErrorData } from "hls.js";
import { resolveHlsUrl } from "../../common/utils/hls.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import Loader from "../ui/Loader/Loader.tsx";

type Props = {
  srcMp4: string;
  poster?: string;
  className?: string;
  autoPlay?: boolean;
  controls?: boolean;
  loop?: boolean;
  muted?: boolean;
  preferHls?: boolean; // по умолчанию false (стримим MP4; HLS включаем явно)
};

const externalHosts = [
  "play.boomstream.com",
  "player.vimeo.com",
  "vimeo.com",
  "kinescope.io",
  "vk.com",
];

const DEBUG_HLS_RANGE = Boolean(import.meta.env?.DEV);

const MP4_MEDIA_HOST = "media.dent-s.com";
const CDN_HOST = "cdn.dent-s.com";

const normalizeVideoKey = (url: string): string => {
  try {
    const u = new URL(url);
    // ключ должен быть стабилен между cdn/media и не зависеть от query/host
    // (host меняется cdn↔media, а pathname указывает на один и тот же объект)
    return `${u.pathname}`.toLowerCase();
  } catch {
    return String(url || "").toLowerCase();
  }
};

const markMp4Ok = (key: string) => {
  try {
    const LS_KEY = "video_mp4_ok_v1";
    const raw = localStorage.getItem(LS_KEY);
    const map = raw ? (JSON.parse(raw) as Record<string, number>) : {};
    map[key] = Date.now();
    localStorage.setItem(LS_KEY, JSON.stringify(map));
  } catch {
    // ignore
  }
};

const isMp4Ok = (key: string): boolean => {
  try {
    const LS_KEY = "video_mp4_ok_v1";
    const raw = localStorage.getItem(LS_KEY);
    const map = raw ? (JSON.parse(raw) as Record<string, number>) : {};
    const ts = map[key] || 0;
    // считаем "ок" в течение суток (чтобы не спамить ремонтами по рабочим файлам)
    return Date.now() - ts < 24 * 60 * 60 * 1000;
  } catch {
    return false;
  }
};

const toMediaHostMp4Url = (url: string): string => {
  try {
    const u = new URL(url);
    // Не трогаем внешние плееры
    if (externalHosts.some((h) => u.hostname.includes(h))) return url;
    if (u.hostname === MP4_MEDIA_HOST) return url;
    if (u.hostname === CDN_HOST) {
      u.hostname = MP4_MEDIA_HOST;
      return u.toString();
    }
    return url;
  } catch {
    return url;
  }
};

const findAscii = (buf: ArrayBuffer, ascii: string): number => {
  const needle = new TextEncoder().encode(ascii);
  const hay = new Uint8Array(buf);
  outer: for (let i = 0; i <= hay.length - needle.length; i++) {
    for (let j = 0; j < needle.length; j++) {
      if (hay[i + j] !== needle[j]) continue outer;
    }
    return i;
  }
  return -1;
};

const parseTotalFromContentRange = (cr: string | null): number | null => {
  // "bytes 0-0/4726368866"
  if (!cr) return null;
  const m = /\/(\d+)\s*$/i.exec(cr);
  if (!m) return null;
  const n = Number(m[1]);
  return Number.isFinite(n) && n > 0 ? n : null;
};

type FaststartProbeResult = "faststart_ok" | "no_faststart" | "unknown";

const probeFaststartByRange = async (url: string): Promise<FaststartProbeResult> => {
  const PROBE_BYTES = 2 * 1024 * 1024; // 2MB

  // 1) небольшой кусок с начала — ищем 'moov'
  const headResp = await fetch(url, {
    method: "GET",
    mode: "cors",
    cache: "no-store",
    headers: { Range: `bytes=0-${PROBE_BYTES - 1}` }, // 2MB
  });
  if (!headResp.ok && headResp.status !== 206) return "unknown";
  const headBuf = await headResp.arrayBuffer();
  const moovInHead = findAscii(headBuf, "moov") !== -1;
  if (moovInHead) return "faststart_ok";

  // 2) Узнаём total через очень маленький Range (0-0) → Content-Range
  const metaResp = await fetch(url, {
    method: "GET",
    mode: "cors",
    cache: "no-store",
    headers: { Range: "bytes=0-0" },
  });
  const total = parseTotalFromContentRange(metaResp.headers.get("Content-Range"));
  if (!total) return "unknown";

  // 3) кусок с хвоста — если там есть 'moov', то это почти наверняка “moov в конце”
  const tailStart = Math.max(total - PROBE_BYTES, 0);
  const tailResp = await fetch(url, {
    method: "GET",
    mode: "cors",
    cache: "no-store",
    headers: { Range: `bytes=${tailStart}-${total - 1}` },
  });
  if (!tailResp.ok && tailResp.status !== 206) return "unknown";
  const tailBuf = await tailResp.arrayBuffer();
  const moovInTail = findAscii(tailBuf, "moov") !== -1;
  return moovInTail ? "no_faststart" : "unknown";
};

const isSegmentUrl = (url: string): boolean => {
  const u = (url || "").toLowerCase();
  // учитываем query-string: ".ts?x=1"
  return u.includes(".ts") || u.includes(".m4s") || u.includes(".aac");
};

const addCacheBustParam = (url: string): string => {
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}r=${Date.now()}`;
};

const isProbablySafari = (): boolean => {
  // Chrome тоже может вернуть "maybe" на canPlayType для m3u8, но реально проигрывать не будет/будет нестабильно.
  // Поэтому нативный HLS включаем только для Safari/iOS, а в остальных браузерах всегда используем hls.js.
  try {
    const ua = navigator.userAgent.toLowerCase();
    const isSafari = ua.includes("safari") && !ua.includes("chrome") && !ua.includes("chromium") && !ua.includes("android");
    return isSafari;
  } catch {
    return false;
  }
};

// Жёсткое отключение Range на уровне hls.js loader context
// В некоторых версиях простого delete недостаточно: внутренний код проверяет наличие поля,
// поэтому дополнительно выставляем rangeStart/rangeEnd = undefined.
const hardStripRangeFromContext = (ctx: any) => {
  if (!ctx || typeof ctx !== "object") return;
  try {
    // eslint-disable-next-line no-prototype-builtins
    if (ctx.hasOwnProperty("rangeStart")) delete ctx.rangeStart;
    // eslint-disable-next-line no-prototype-builtins
    if (ctx.hasOwnProperty("rangeEnd")) delete ctx.rangeEnd;
  } catch {
    // ignore
  }
  try {
    // принудительно “обнуляем” (важно!)
    ctx.rangeStart = undefined;
    ctx.rangeEnd = undefined;
  } catch {
    // ignore
  }
  try {
    const headers = ctx.headers;
    if (headers && typeof headers === "object") {
      const hadRange = ("Range" in headers) || ("range" in headers);
      if ("Range" in headers) delete headers.Range;
      if ("range" in headers) delete headers.range;
      if (DEBUG_HLS_RANGE && hadRange) {
        console.debug("[HLS][NoRange] stripped Range from context.headers for", String(ctx?.url ?? ""));
      }
    }
  } catch {
    // ignore
  }
};

// Таймауты HLS: базовые значения (обычное воспроизведение)
// ВАЖНО: при нестабильном соединении CF↔origin возможны “длинные” сегменты (10–20s+).
// Если держать 25s, hls.js будет абортить и вы получите (canceled) + ретраи => "видео обрывками".
// На MISS сегмент иногда реально тянется дольше минуты (CF↔origin). Если ставить 60s — будет вечный abort/retry первого сегмента.
const NORMAL_TIMEOUT_MS = 180000; // базовый таймаут загрузки фрагмента (до 180s)
const SEEK_TIMEOUT_MS = 30000; // увеличенный таймаут в режиме перемотки
// Максимальная «длительность seek-окна» не должна быть меньше, чем один полный цикл фрагмента + несколько retry
// SEEK_TIMEOUT_MS(30s) + retryDelay(1s)*2 + запас => минимум ~35s; ставим 45s как дефолт
const SEEK_MAX_DURATION_MS = 45000;
const SEEK_FAILS_BEFORE_FALLBACK = 2; // диагностический счётчик подряд таймаутов в seekMode
const SEEK_NO_PROGRESS_MS = 12000; // нет роста буфера около currentTime за последние X мс => считаем, что прогресса нет
const SEEK_QUIET_MS = 1500; // «тихое окно» после seeking: не считаем ошибки/фейлы сразу
const FRAG_BYTES_PROGRESS_RECENT_MS = 4000; // если байты фрагмента росли недавно — считаем, что есть прогресс

// Таймер “первого сегмента” (hls.js): не фолбэчим, если есть признаки прогресса
// ВАЖНО: сегмент может реально грузиться 15–20s+ из-за CF↔origin/edge MISS.
// Поэтому НЕ делаем MP4 fallback по 15s — вместо этого даём время + делаем несколько циклов recovery.
const FIRST_FRAG_TIMEOUT_MS = 180000;
const FIRST_FRAG_NO_PROGRESS_MS = 10000; // окно “байтового” прогресса, чтобы не считать старт “мертвым”
const FIRST_FRAG_RECOVERY_MAX_CYCLES = 3;

// Anti-flap: не уходим в MP4 по первому fatal — сначала recovery, только затем fallback
const FATAL_WINDOW_MS = 12000;
const FATAL_RECOVERY_MAX_ATTEMPTS = 2; // 1–2 попытки recovery на окно
const FATAL_OTHER_MAX_ATTEMPTS = 2; // для “прочих” fatal даём 1 попытку (на 2-й — fallback)

// Конфигурация HLS (умеренные таймауты/ретраи, чтобы переживать кратковременные сбои/просадки)
const HLS_CONFIG: Partial<Hls["config"]> = {
  enableWorker: true,
  lowLatencyMode: false,
  progressive: false,
  // Принудительно используем XHR loader, чтобы xhrSetup гарантированно применялся
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  loader: ((Hls as any).XhrLoader ?? (Hls as any).DefaultConfig?.loader) as any,
  autoStartLoad: true,
  // ВАЖНО: не форсим startPosition=0 — это может резко увеличить параллельные обращения к Worker↔origin
  // и спровоцировать "Network connection lost". Пусть hls.js сам выбирает стартовую позицию.
  startPosition: -1,
  
  // Буферизация
  // Увеличиваем “подушку” буфера, чтобы переживать редкие медленные сегменты без stall
  // Держим достаточно большой “запас вперёд”, чтобы медленный/проблемный сегмент успевал ретраиться,
  // пока ещё есть буфер для воспроизведения.
  backBufferLength: 60,
  maxBufferLength: 180,
  maxMaxBufferLength: 360,
  // maxBufferLength ограничивается ещё и maxBufferSize (байты). На ваших сегментах 60MB слишком мало.
  maxBufferSize: 300 * 1000 * 1000,
  maxBufferHole: 0.5,
  
  // Главное изменение №1 (обязательно): No-Range на 100% через xhrSetup
  // Важно: xhr.setRequestHeader("Range","") не везде “очищает” заголовок — надёжнее НЕ давать его выставить.
  // Плюс: не даём появиться Cache-Control: no-cache, если кто-то начнёт ставить вручную.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  xhrSetup: (xhr: any, url: string) => {
    try {
      if (!xhr) return;

      // A) Жёстко блокируем Range по “маркеру сегмента”
      const markSegment = (u: string) => {
        try {
          xhr.__hls_last_url = u;
          xhr.__hls_is_segment = isSegmentUrl(u);
        } catch {
          // ignore
        }
      };

      // url из аргумента xhrSetup может отличаться от фактического url в open()
      markSegment(String(url || ""));

      // B) wrap open(): помечаем xhr как “сегмент” по реальному URL
      try {
        if (!xhr.__hls_open_wrapped && typeof xhr.open === "function") {
          const origOpen = xhr.open;
          // Важно: не “дополняем” аргументы сами — иначе можно случайно сделать sync XHR (async=false).
          // Проксируем как есть, чтобы сохранить семантику вызова в hls.js/браузере.
          xhr.open = function (...args: any[]) {
            const u = args?.[1];
            markSegment(String(u || ""));
            // eslint-disable-next-line prefer-rest-params
            return origOpen.apply(xhr, args);
          };
          xhr.__hls_open_wrapped = true;
        }
      } catch {
        // ignore
      }

      // wrap setRequestHeader(): НЕ даём установить Range для сегментов
      try {
        if (!xhr.__hls_setheader_wrapped && typeof xhr.setRequestHeader === "function") {
          const original = xhr.setRequestHeader.bind(xhr);
          xhr.setRequestHeader = (name: string, value: string) => {
            const lname = String(name || "").toLowerCase();
            const isSeg = Boolean(xhr.__hls_is_segment) || isSegmentUrl(String(xhr.__hls_last_url || url || ""));

            if (isSeg && lname === "range") {
              try {
                xhr.__hls_range_blocked = true;
              } catch {
                // ignore
              }
              if (DEBUG_HLS_RANGE) {
                console.debug("[HLS][NoRange] blocked XHR Range header for", String(xhr.__hls_last_url || url || ""));
              }
              // No-Range: игнорируем
              return;
            }
            if (lname === "cache-control" && String(value || "").toLowerCase().includes("no-cache")) {
              // не добавляем “no-cache” вручную
              return;
            }
            original(name, value);
          };
          xhr.__hls_setheader_wrapped = true;
        }
      } catch {
        // ignore
      }

      // wrap send(): финальная точка перед отправкой
      // У XHR нет API “удалить уже выставленный заголовок”, поэтому:
      // - мы блокируем Range в setRequestHeader (главное)
      // - и дополнительно чистим возможные внутренние “кэши заголовков” (если они есть у конкретной реализации)
      try {
        if (!xhr.__hls_send_wrapped && typeof xhr.send === "function") {
          const origSend = xhr.send;
          xhr.send = function (...args: any[]) {
            const isSeg = Boolean(xhr.__hls_is_segment) || isSegmentUrl(String(xhr.__hls_last_url || url || ""));
            if (isSeg) {
              try {
                // некоторые реализации/обёртки XHR держат headers в приватных полях
                if (xhr._headers && typeof xhr._headers === "object") {
                  if ("Range" in xhr._headers) delete xhr._headers.Range;
                  if ("range" in xhr._headers) delete xhr._headers.range;
                }
              } catch {
                // ignore
              }
            }
            // eslint-disable-next-line prefer-rest-params
            return origSend.apply(xhr, args);
          };
          xhr.__hls_send_wrapped = true;
        }
      } catch {
        // ignore
      }
    } catch {
      // ignore
    }
  },

  // Если hls.js (или окружение) переключится на FetchLoader — тоже режем Range
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fetchSetup: async (context: any, initParams: any) => {
    const url = String(context?.url ?? "");
    const isSeg = isSegmentUrl(url) || String(context?.type ?? "").toLowerCase() === "fragment";
    if (isSeg && initParams?.headers) {
      const h = initParams.headers;
      try {
        if (typeof (h as Headers).delete === "function") {
          (h as Headers).delete("Range");
          (h as Headers).delete("range");
        } else if (Array.isArray(h)) {
          initParams.headers = h.filter(([k]) => String(k).toLowerCase() !== "range");
        } else if (typeof h === "object") {
          delete h.Range;
          delete h.range;
        }
        if (DEBUG_HLS_RANGE) {
          console.debug("[HLS][NoRange] fetchSetup stripped Range for", url);
        }
      } catch {
        // ignore
      }
    }
    return new Request(url, initParams);
  },

  // Manifest/level: даём CDN/сети шанс “подышать”
  manifestLoadingTimeOut: 15000, // 12–15s
  manifestLoadingMaxRetry: 3,
  manifestLoadingRetryDelay: 1000,
  
  levelLoadingTimeOut: 15000, // 12–15s
  levelLoadingMaxRetry: 3,
  levelLoadingRetryDelay: 1000,
  
  // Фрагменты: не “ломучие”
  fragLoadingTimeOut: NORMAL_TIMEOUT_MS,
  fragLoadingMaxRetry: 3,
  fragLoadingRetryDelay: 1200,
  
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
  // По умолчанию: без HLS (чтобы не дёргать m3u8/сегменты и опираться на стабильный MP4 Range=206)
  preferHls = false,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const hlsRef = useRef<Hls | null>(null);
  const [useMp4Fallback, setUseMp4Fallback] = useState(!preferHls);
  const [hlsUrl, setHlsUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // MP4 должен идти через отдельный поддомен (DNS only), чтобы не проксироваться через Cloudflare
  const mp4PlaybackUrl = toMediaHostMp4Url(srcMp4);
  const mp4Key = normalizeVideoKey(mp4PlaybackUrl);
  
  // Ref для таймеров чтобы очищать их
  const fallbackTimerRef = useRef<number | null>(null);
  const playbackStartedRef = useRef(false);

  // seekMode: активируется только на время перемотки, чтобы не ловить ложные fallback из-за CDN MISS→HIT
  const seekModeRef = useRef(false);
  const seekFailsRef = useRef(0);
  const seekGraceTimerRef = useRef<number | null>(null);
  const seekMonitorTimerRef = useRef<number | null>(null);
  const seekQuietUntilRef = useRef(0);
  const seekLastProgressAtRef = useRef(0);
  const seekLastBufferedAheadRef = useRef(0);
  const seekSoftExpiredRef = useRef(false);
  const normalFragConfigRef = useRef<{
    fragLoadingTimeOut: number;
    fragLoadingMaxRetry: number;
    fragLoadingRetryDelay: number;
  } | null>(null);

  // Прогресс загрузки фрагмента (bytes). Нужен, чтобы не делать ложный fallback при timeout, когда загрузка реально идёт.
  const fragBytesLastLoadedRef = useRef(0);
  const fragBytesLastAtRef = useRef(0);
  const fragBytesUrlRef = useRef<string | null>(null);
  const fragBytesInFlightRef = useRef(false);

  // Счётчики fatal для recovery (anti-flap)
  const fatalNetworkRef = useRef<{ windowStart: number; attempts: number }>({ windowStart: 0, attempts: 0 });
  const fatalMediaRef = useRef<{ windowStart: number; attempts: number }>({ windowStart: 0, attempts: 0 });
  const fatalOtherRef = useRef<{ windowStart: number; attempts: number }>({ windowStart: 0, attempts: 0 });
  const demuxRecoverRef = useRef<{ windowStart: number; attempts: number }>({ windowStart: 0, attempts: 0 });

  // Cache-bust попытки должны переживать пересоздание loader-а (в hls.js loader одноразовый).
  // Поэтому держим счётчики на уровне компонента, а не внутри loader instance.
  const cacheBustAttemptsRef = useRef<Map<string, number>>(new Map());
  const firstFragRecoverRef = useRef<{ windowStart: number; attempts: number }>({ windowStart: 0, attempts: 0 });

  // MP4 faststart: авто-триггер задачи переноса moov atom, если старт MP4 не идёт
  const faststartProbeTimerRef = useRef<number | null>(null);
  const faststartRequestedRef = useRef<Set<string>>(new Set()); // mp4Key
  const faststartPollTimerRef = useRef<number | null>(null);
  const faststartStartupTimerRef = useRef<number | null>(null);
  const faststartEnsureInFlightRef = useRef(false);
  const mp4OkRef = useRef<Set<string>>(new Set()); // mp4Key

  const [faststartUi, setFaststartUi] = useState<{
    phase: "idle" | "queued" | "running" | "done" | "error";
    taskId?: string;
    message?: string;
  }>({ phase: "idle" });

  // Очистка таймеров
  const clearFallbackTimer = useCallback(() => {
    if (fallbackTimerRef.current) {
      window.clearTimeout(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
  }, []);

  const clearSeekGraceTimer = useCallback(() => {
    if (seekGraceTimerRef.current) {
      window.clearTimeout(seekGraceTimerRef.current);
      seekGraceTimerRef.current = null;
    }
  }, []);

  const clearSeekMonitorTimer = useCallback(() => {
    if (seekMonitorTimerRef.current) {
      window.clearInterval(seekMonitorTimerRef.current);
      seekMonitorTimerRef.current = null;
    }
  }, []);

  const clearFaststartProbeTimer = useCallback(() => {
    if (faststartProbeTimerRef.current) {
      window.clearTimeout(faststartProbeTimerRef.current);
      faststartProbeTimerRef.current = null;
    }
  }, []);

  const clearFaststartPollTimer = useCallback(() => {
    if (faststartPollTimerRef.current) {
      window.clearInterval(faststartPollTimerRef.current);
      faststartPollTimerRef.current = null;
    }
  }, []);

  const clearFaststartStartupTimer = useCallback(() => {
    if (faststartStartupTimerRef.current) {
      window.clearTimeout(faststartStartupTimerRef.current);
      faststartStartupTimerRef.current = null;
    }
  }, []);

  const shouldThrottleFaststartRequest = useCallback((key: string): boolean => {
    try {
      const LS_KEY = "video_faststart_requested_v1";
      const raw = localStorage.getItem(LS_KEY);
      const map = raw ? (JSON.parse(raw) as Record<string, number>) : {};
      const now = Date.now();
      const last = map[key] || 0;
      const COOLDOWN_MS = 10 * 60 * 1000; // 10 минут
      if (now - last < COOLDOWN_MS) return true;
      map[key] = now;
      localStorage.setItem(LS_KEY, JSON.stringify(map));
      return false;
    } catch {
      return false;
    }
  }, []);

  const maybeRequestFaststart = useCallback(
    (reason: string, delayMs: number = 4000) => {
      const video = videoRef.current;
      if (!video) return;
      // Только для MP4-режима
      if (!useMp4Fallback || preferHls) return;
      if (playbackStartedRef.current) return;
      if ((video.currentTime || 0) > 0.5) return;
      if (mp4OkRef.current.has(mp4Key) || isMp4Ok(mp4Key)) return;
      if (faststartRequestedRef.current.has(mp4Key)) return;
      if (faststartEnsureInFlightRef.current) return;
      if (faststartUi.phase !== "idle") return;

      // Доп. дедуп на уровне localStorage, чтобы не спамить при перезагрузках/ремонтах/повторах.
      if (shouldThrottleFaststartRequest(mp4Key)) return;

      console.warn("[Video][MP4] maybeRequestFaststart scheduled:", { reason, delayMs, src: srcMp4 });

      // не штурмим — ставим задержку, чтобы не реагировать на краткие "waiting"
      clearFaststartProbeTimer();
      // Считаем “запрошено” уже на стадии планирования, чтобы серия событий не создала пачку POST.
      faststartRequestedRef.current.add(mp4Key);
      faststartProbeTimerRef.current = window.setTimeout(async () => {
        try {
          // перепроверяем состояние
          const v = videoRef.current;
          if (!v) return;
          if (playbackStartedRef.current) return;
          if ((v.currentTime || 0) > 0.5) return;

          // Важно: client-side probe может не сработать (CORS/Range/preflight, moov вне окна и т.п.).
          // Поэтому всегда дергаем backend ensure-faststart: он сам проверит moov/mdat (ffprobe) и решит, ставить задачу или нет.
          let probe: FaststartProbeResult = "unknown";
          try {
            probe = await probeFaststartByRange(mp4PlaybackUrl);
          } catch {
            // ignore
          }

          faststartEnsureInFlightRef.current = true;
          console.warn("[Video][MP4] Requesting backend ensure-faststart...", {
            reason,
            probe,
            src: mp4PlaybackUrl,
          });
          setFaststartUi({
            phase: "queued",
            message: "Прямо сейчас исправляем видео (переносим метаданные MP4 для быстрого старта)…",
          });
          const resp = await mainApi.ensureFaststart(mp4PlaybackUrl, reason);
          const status = String(resp?.data?.status || "");
          const taskId = resp?.data?.task_id as string | undefined;
          console.warn("[Video][MP4] ensure-faststart response:", { status, taskId });
          if (status === "queued" && taskId) {
            setFaststartUi((s) => ({ ...s, phase: "queued", taskId }));
          } else if (status === "skipped") {
            setFaststartUi({ phase: "idle" });
          } else if (status === "cooldown") {
            // уже запрашивали недавно — просто оставляем UI и ждём polling без task_id (по metadata)
            setFaststartUi((s) => ({ ...s, phase: "queued" }));
          } else if (status === "unknown") {
            setFaststartUi({
              phase: "error",
              message: "Не удалось определить, нужен ли faststart. Попробуйте позже.",
            });
          }
        } catch (e) {
          // не ломаем воспроизведение из-за диагностики
          console.warn("[Video][MP4] faststart probe/request failed:", e);
          setFaststartUi({
            phase: "error",
            message: "Не удалось запустить автоматическое исправление. Попробуйте обновить страницу или повторить позже.",
          });
        } finally {
          faststartEnsureInFlightRef.current = false;
        }
      }, delayMs);
    },
    [
      clearFaststartProbeTimer,
      preferHls,
      srcMp4,
      mp4PlaybackUrl,
      mp4Key,
      shouldThrottleFaststartRequest,
      useMp4Fallback,
      faststartUi.phase,
    ],
  );

  // Polling статуса faststart: показываем пользователю прогресс и по завершению обновляем страницу
  useEffect(() => {
    if (faststartUi.phase === "idle" || faststartUi.phase === "done" || faststartUi.phase === "error") {
      clearFaststartPollTimer();
      return;
    }
    // Poll только для MP4-режима
    if (!useMp4Fallback || preferHls) {
      clearFaststartPollTimer();
      return;
    }

    const startedAt = Date.now();
    const MAX_POLL_MS = 20 * 60 * 1000; // 20 минут

    clearFaststartPollTimer();
    const pollIntervalMs = faststartUi.taskId ? 5000 : 30000; // без taskId (cooldown) проверяем метаданные реже
    faststartPollTimerRef.current = window.setInterval(async () => {
      try {
        if (Date.now() - startedAt > MAX_POLL_MS) {
          clearFaststartPollTimer();
          setFaststartUi({
            phase: "error",
            taskId: faststartUi.taskId,
            message: "Исправление занимает слишком много времени. Попробуйте обновить страницу позже.",
          });
          return;
        }

        const st = await mainApi.getFaststartStatus(mp4PlaybackUrl, faststartUi.taskId);
        const data = st?.data;
        const faststart = Boolean(data?.faststart);
        const state = String(data?.task_state || "");

        if (faststart || state === "SUCCESS") {
          clearFaststartPollTimer();
          setFaststartUi({
            phase: "done",
            taskId: faststartUi.taskId,
            message: "Готово. Сейчас обновим страницу…",
          });
          window.setTimeout(() => window.location.reload(), 1500);
          return;
        }

        if (state === "FAILURE") {
          clearFaststartPollTimer();
          setFaststartUi({
            phase: "error",
            taskId: faststartUi.taskId,
            message: "Не удалось исправить видео автоматически. Мы уже работаем над этим — попробуйте позже.",
          });
          return;
        }

        setFaststartUi((s) => ({
          ...s,
          phase: state === "STARTED" ? "running" : "queued",
          message:
            state === "STARTED"
              ? "Исправляем видео (это может занять несколько минут)…"
              : faststartUi.taskId
                ? "Готовим исправление для видео…"
                : "Исправление уже запущено. Проверяем статус…",
        }));
      } catch (e) {
        // временные ошибки polling не валим сразу — просто оставляем текущий статус
      }
    }, pollIntervalMs);

    return () => {
      clearFaststartPollTimer();
    };
  }, [clearFaststartPollTimer, faststartUi.phase, faststartUi.taskId, preferHls, mp4PlaybackUrl, useMp4Fallback]);

  // БЫСТРЫЙ fallback на MP4
  const fallbackToMp4 = useCallback(() => {
    console.log("[HLS] FAST fallback to MP4:", mp4PlaybackUrl);
    
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
      videoRef.current.src = mp4PlaybackUrl;
      videoRef.current.load();
    }
  }, [mp4PlaybackUrl, clearFallbackTimer]);

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
    clearSeekGraceTimer();
    clearSeekMonitorTimer();
    playbackStartedRef.current = false;
    seekModeRef.current = false;
    seekFailsRef.current = 0;
    seekQuietUntilRef.current = 0;
    seekLastProgressAtRef.current = 0;
    seekLastBufferedAheadRef.current = 0;
    seekSoftExpiredRef.current = false;
    normalFragConfigRef.current = null;
    fragBytesLastLoadedRef.current = 0;
    fragBytesLastAtRef.current = 0;
    fragBytesUrlRef.current = null;
    fragBytesInFlightRef.current = false;
    fatalNetworkRef.current = { windowStart: 0, attempts: 0 };
    fatalMediaRef.current = { windowStart: 0, attempts: 0 };
    fatalOtherRef.current = { windowStart: 0, attempts: 0 };
    demuxRecoverRef.current = { windowStart: 0, attempts: 0 };
    cacheBustAttemptsRef.current = new Map();
    firstFragRecoverRef.current = { windowStart: 0, attempts: 0 };

    // Очищаем предыдущий hls instance
    if (hlsRef.current) {
      try {
        hlsRef.current.destroy();
      } catch {}
      hlsRef.current = null;
    }

    // MP4 фолбэк или HLS не найден
    if (!preferHls || useMp4Fallback || !hlsUrl) {
      console.log("[Video] Using MP4 source:", mp4PlaybackUrl);
      video.src = mp4PlaybackUrl;
      video.load();

      // Если MP4 не стартует “в начале” за разумное время — запускаем faststart probe сами (не дожидаясь waiting/stalled).
      // Это покрывает случаи, когда браузер не генерирует события, но всё равно пытается читать хвост файла.
      clearFaststartStartupTimer();
      faststartStartupTimerRef.current = window.setTimeout(() => {
        const v = videoRef.current;
        if (!v) return;
        if (playbackStartedRef.current) return;
        if ((v.currentTime || 0) > 0.5) return;
        // Быстрый запуск probe без дополнительной задержки
        maybeRequestFaststart("startup_timeout", 0);
      }, 9000);

      return;
    }

    // hls.js: ВАЖНО — если поддерживается, используем ВСЕГДА.
    // Иначе Chromium может пойти в “квази-нативный” HLS, где сегменты грузит media pipeline с Range: bytes=0-,
    // и это невозможно отключить снаружи (что вы и видите в DevTools).
    if (Hls.isSupported()) {
      console.log("[HLS] Initializing hls.js for:", hlsUrl);
      const DefaultLoader = (Hls as any).DefaultConfig?.loader;
      const ProgressFragmentLoader = DefaultLoader
        ? class {
            private inner: any;
            constructor(config: any) {
              this.inner = new DefaultLoader(config);
            }
            // ВАЖНО для hls.js: FragmentLoader читает loader.stats и сохраняет в frag.stats/part.stats.
            // Если stats не прокинуть — AbrController падает на stats.loading.start.
            get stats() {
              return this.inner?.stats;
            }
            destroy() {
              this.inner?.destroy?.();
            }
            abort() {
              this.inner?.abort?.();
            }
            load(context: any, config: any, callbacks: any) {
              const rawUrl = String(context?.url ?? "");
              const isFragType = String(context?.type ?? "").toLowerCase() === "fragment";
              const segmentLike = isFragType || isSegmentUrl(rawUrl);

              const stripRangeFromContext = (ctx: any) => {
                hardStripRangeFromContext(ctx);
              };

              // 1) Главное изменение: запрет Range для HLS сегментов
              // Убираем любые признаки range-загрузки для .ts/.m4s/.aac, чтобы снизить риск HTTP/2 RST_STREAM в Chromium/MSE.
              try {
                if (segmentLike) stripRangeFromContext(context);
              } catch {
                // ignore
              }

              const getAttemptsKey = (u: string): string => {
                // удаляем только наш cache-bust параметр r=..., если он есть
                try {
                  const parsed = new URL(u);
                  parsed.searchParams.delete("r");
                  return parsed.toString();
                } catch {
                  return u.replace(/[?&]r=\d+/g, "");
                }
              };

              // ВАЖНО: НЕ делаем this.inner.load() повторно изнутри callbacks.
              // Некоторые loaders (например FetchLoader) одноразовые и падают с "Loader can only be used once".
              // Вместо этого помечаем, что СЛЕДУЮЩАЯ попытка должна идти с cache-bust параметром.
              const markCacheBustForNextAttempt = (reason: string): boolean => {
                if (!segmentLike) return false;
                const key = getAttemptsKey(String(context?.url ?? ""));
                const prev = cacheBustAttemptsRef.current.get(key) ?? 0;
                const next = prev + 1;
                if (next > 2) return false;
                cacheBustAttemptsRef.current.set(key, next);
                const bustedUrl = addCacheBustParam(key);
                console.warn(`[HLS] loader mark cache-bust #${next}/2 reason=${reason} nextUrl=${bustedUrl}`);
                return true;
              };

              // Если это уже повторная попытка — подставляем cache-bust URL перед реальным load()
              if (segmentLike) {
                const key = getAttemptsKey(rawUrl);
                const attempt = cacheBustAttemptsRef.current.get(key) ?? 0;
                if (attempt > 0) {
                  const bustedUrl = addCacheBustParam(key);
                  if (DEBUG_HLS_RANGE) {
                    console.debug(`[HLS] applying cache-bust attempt=${attempt}/2 url=${bustedUrl}`);
                  }
                  context.url = bustedUrl;
                }
              }

              // Перед реальным load() ещё раз жёстко вычищаем Range, т.к. FragmentLoader по умолчанию ставит rangeStart/rangeEnd=0
              if (segmentLike) {
                stripRangeFromContext(context);
              }

              const wrappedCallbacks = {
                ...callbacks,
                onProgress: (stats: any, ctx: any, data: any, networkDetails: any) => {
                  callbacks?.onProgress?.(stats, ctx, data, networkDetails);
                  try {
                    const loaded = Number(stats?.loaded ?? 0);
                    if (loaded > fragBytesLastLoadedRef.current) {
                      fragBytesLastLoadedRef.current = loaded;
                      fragBytesLastAtRef.current = Date.now();
                      // если мы в seekMode — это тоже “прогресс”, даже если buffered ещё не вырос
                      if (seekModeRef.current) {
                        seekLastProgressAtRef.current = fragBytesLastAtRef.current;
                      }
                    }
                  } catch {
                    // ignore
                  }
                },
                onTimeout: (stats: any, ctx: any, networkDetails: any) => {
                  markCacheBustForNextAttempt("timeout");
                  callbacks?.onTimeout?.(stats, ctx, networkDetails);
                },
                onError: (error: any, ctx: any, networkDetails: any) => {
                  // Сетевые ошибки по сегментам (status=0 и т.п.) пробуем “дожать” cache-bust retry
                  const status =
                    Number(error?.code ?? 0) || Number(networkDetails?.xhr?.status ?? 0) || Number(ctx?.response?.code ?? 0) || 0;
                  const text = String(error?.text ?? error?.message ?? "").toLowerCase();
                  const looksNetworky =
                    status === 0 ||
                    status >= 500 ||
                    text.includes("network") ||
                    text.includes("http2") ||
                    text.includes("protocol");
                  if (looksNetworky) {
                    markCacheBustForNextAttempt(`network status=${status}`);
                  }
                  callbacks?.onError?.(error, ctx, networkDetails);
                },
                onSuccess: (response: any, stats: any, ctx: any, networkDetails: any) => {
                  // Если “успех”, но тело похоже на неполное — считаем это ошибкой и делаем cache-bust retry.
                  // Часто проявляется как DEMUXER_ERROR/FRAG_PARSING_ERROR на обрезанном TS.
                  if (segmentLike) {
                    const loaded = Number(stats?.loaded ?? 0);
                    const total = Number(stats?.total ?? 0);
                    let actual = 0;
                    try {
                      const d = response?.data;
                      if (d && typeof d.byteLength === "number") actual = d.byteLength;
                    } catch {
                      // ignore
                    }

                    const expected = total > 0 ? total : 0;
                    const hasExpected = expected > 0;
                    const hasLoaded = loaded > 0;
                    const isTruncated =
                      (hasExpected && hasLoaded && loaded < expected) || (hasExpected && !hasLoaded && actual > 0 && actual < expected);

                    if (isTruncated) {
                      const reason = `truncated loaded=${loaded} total=${total} actual=${actual}`;
                      markCacheBustForNextAttempt(reason);
                    }
                  }

                  // Успех по сегменту — сбрасываем cache-bust попытки для базового URL, чтобы не “мутить” URL бесконечно
                  if (segmentLike) {
                    const key = getAttemptsKey(String(ctx?.url ?? rawUrl));
                    if (cacheBustAttemptsRef.current.get(key)) {
                      cacheBustAttemptsRef.current.delete(key);
                    }
                  }

                  callbacks?.onSuccess?.(response, stats, ctx, networkDetails);
                },
              };
              this.inner.load(context, config, wrappedCallbacks);
            }
          }
        : undefined;

      const hls = new Hls({
        ...HLS_CONFIG,
        ...(ProgressFragmentLoader ? { fLoader: ProgressFragmentLoader as any } : {}),
      });
      hlsRef.current = hls;

      let firstFragLoaded = false;
      let destroyed = false;

      const getBufferedAheadSeconds = (): number => {
        try {
          const t = video.currentTime;
          const b = video.buffered;
          for (let i = 0; i < b.length; i += 1) {
            const start = b.start(i);
            const end = b.end(i);
            if (t >= start && t <= end) {
              return Math.max(0, end - t);
            }
          }
        } catch {
          // ignore
        }
        return 0;
      };

      const markBufferProgressIfAny = (reason: "BUFFER_GROWTH" | "PLAYING") => {
        if (!seekModeRef.current) return;
        const ahead = getBufferedAheadSeconds();
        const prevAhead = seekLastBufferedAheadRef.current;
        // рост буфера около currentTime — надёжный признак прогресса
        if (ahead > prevAhead + 0.25) {
          seekLastBufferedAheadRef.current = ahead;
          seekLastProgressAtRef.current = Date.now();
          seekSoftExpiredRef.current = false;
          console.log(`[HLS] seek buffer progress ahead=${ahead.toFixed(2)}s reason=${reason}`);
          exitSeekMode("BUFFER_GROWTH");
        }
      };

      const exitSeekMode = (reason: "BUFFER_GROWTH" | "PLAYING" | "FALLBACK") => {
        if (!seekModeRef.current) return;
        console.log(`[HLS] seekMode EXIT reason=${reason}`);
        seekModeRef.current = false;
        seekFailsRef.current = 0;
        seekSoftExpiredRef.current = false;
        clearSeekGraceTimer();
        clearSeekMonitorTimer();

        const normal = normalFragConfigRef.current;
        if (normal) {
          try {
            hls.config.fragLoadingTimeOut = normal.fragLoadingTimeOut;
            hls.config.fragLoadingMaxRetry = normal.fragLoadingMaxRetry;
            hls.config.fragLoadingRetryDelay = normal.fragLoadingRetryDelay;
          } catch (e) {
            console.warn("[HLS] Failed to restore normal frag config:", e);
          }
        }
      };

      const onVideoSeeking = () => {
        if (destroyed) return;
        if (seekModeRef.current) return;

        console.log("[HLS] seekMode ENTER");
        seekModeRef.current = true;
        seekFailsRef.current = 0;
        seekSoftExpiredRef.current = false;
        seekQuietUntilRef.current = Date.now() + SEEK_QUIET_MS;
        seekLastProgressAtRef.current = Date.now();
        seekLastBufferedAheadRef.current = getBufferedAheadSeconds();

        // Сохраняем normal-конфиг один раз на инстанс
        if (!normalFragConfigRef.current) {
          normalFragConfigRef.current = {
            fragLoadingTimeOut: hls.config.fragLoadingTimeOut,
            fragLoadingMaxRetry: hls.config.fragLoadingMaxRetry,
            fragLoadingRetryDelay: hls.config.fragLoadingRetryDelay,
          };
        }

        // Применяем seek-конфиг на лету
        try {
          hls.config.fragLoadingTimeOut = SEEK_TIMEOUT_MS;
          hls.config.fragLoadingMaxRetry = 6;
          hls.config.fragLoadingRetryDelay = 1000;
        } catch (e) {
          console.warn("[HLS] Failed to apply seek frag config:", e);
        }

        clearSeekGraceTimer();
        seekGraceTimerRef.current = window.setTimeout(() => {
          if (destroyed) return;
          if (!seekModeRef.current) return;
          // ВАЖНО: таймер не должен «выбивать» из seekMode до окончания реальных попыток hls.js.
          // Делаем мягкую деградацию: возвращаем normal-конфиг, но seekMode оставляем включенным,
          // чтобы следующий FRAG_LOAD_TIMEOUT / fatal не привёл к мгновенному MP4 fallback.
          seekSoftExpiredRef.current = true;
          console.warn("[HLS] seekMode SOFT_EXPIRE (restore normal config, keep seekMode=true)");
          const normal = normalFragConfigRef.current;
          if (normal) {
            try {
              hls.config.fragLoadingTimeOut = normal.fragLoadingTimeOut;
              hls.config.fragLoadingMaxRetry = normal.fragLoadingMaxRetry;
              hls.config.fragLoadingRetryDelay = normal.fragLoadingRetryDelay;
            } catch (e) {
              console.warn("[HLS] Failed to restore normal frag config (soft-expire):", e);
            }
          }
        }, SEEK_MAX_DURATION_MS);

        // Монитор прогресса по video.buffered (правило 3)
        clearSeekMonitorTimer();
        seekMonitorTimerRef.current = window.setInterval(() => {
          if (destroyed) return;
          if (!seekModeRef.current) return;
          markBufferProgressIfAny("BUFFER_GROWTH");
        }, 250);
      };

      const onVideoPlaying = () => {
        if (destroyed) return;
        // playing после seek — тоже хороший признак, но выходим только через buffered-check
        markBufferProgressIfAny("PLAYING");
        if (seekModeRef.current) {
          // если playing случился, но buffered-check не увидел рост (редко), всё равно выходим из seekMode
          exitSeekMode("PLAYING");
        }
      };

      video.addEventListener("seeking", onVideoSeeking);
      video.addEventListener("playing", onVideoPlaying);

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        if (!destroyed) {
          hls.loadSource(hlsUrl);
        }
      });

      hls.on(Hls.Events.MANIFEST_PARSED, (_evt, data) => {
        console.log("[HLS] Manifest loaded:", data.levels.length, "quality levels");
        // Не форсим startLoad(0) здесь: это может раздувать нагрузку на Worker↔origin на старте.
        // autoStartLoad=true уже достаточно для “мягкой” предзагрузки по стратегии hls.js.
        if (autoPlay && !destroyed) {
          video.play().catch(() => {});
        }
      });

      hls.on(Hls.Events.FRAG_LOADING, (_evt: any, data: any) => {
        try {
          fragBytesInFlightRef.current = true;
          fragBytesLastLoadedRef.current = 0;
          fragBytesLastAtRef.current = 0;
          fragBytesUrlRef.current = data?.frag?.url ?? null;
        } catch {
          // ignore
        }
      });

      hls.on(Hls.Events.FRAG_LOADED, () => {
        if (!firstFragLoaded) {
          firstFragLoaded = true;
          playbackStartedRef.current = true;
          clearFallbackTimer();
          console.log("[HLS] First fragment loaded");
        }
        fragBytesInFlightRef.current = false;
        markBufferProgressIfAny("BUFFER_GROWTH");
      });

      hls.on(Hls.Events.BUFFER_APPENDED, () => {
        markBufferProgressIfAny("BUFFER_GROWTH");
      });

      // Ошибки: в seekMode fallback только после N таймаутов + отсутствия роста буфера за последние X секунд
      hls.on(Hls.Events.ERROR, (_evt, data: ErrorData) => {
        if (destroyed) return;
        
        const { type, details, fatal } = data;
        console.warn("[HLS] Error:", type, details, "fatal:", fatal);

        const fragTimeoutDetails =
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          ((Hls as any).ErrorDetails?.FRAG_LOAD_TIMEOUT as unknown) ?? "fragLoadTimeOut";
        const now = Date.now();
        const bytesProgressRecent = now - (fragBytesLastAtRef.current || 0) < FRAG_BYTES_PROGRESS_RECENT_MS;

        // bufferStalledError / bufferSeekOverHole: это “симптом” (буфер просел), а не причина.
        // Вмешательство stopLoad/startLoad часто ухудшает ситуацию (создаёт cancels и сбивает предзагрузку),
        // поэтому здесь НЕ делаем ручной recovery — даём hls.js самому разрулить (GapController/ABR).
        const ErrorDetails = (Hls as any).ErrorDetails;
        const isStallLike =
          String(details || "") === String(ErrorDetails?.BUFFER_STALLED_ERROR ?? "bufferStalledError") ||
          String(details || "") === String(ErrorDetails?.BUFFER_SEEK_OVER_HOLE ?? "bufferSeekOverHole");

        if (isStallLike) {
          return;
        }

        // Demux / parsing ошибки: часто это следствие битого/обрезанного сегмента.
        // Лучшее восстановление — перекачать: stopLoad() -> startLoad(currentTime - smallBackoff).
        const isDemuxLike = (() => {
          const d = String(details || "");
          const known = (Hls as any).ErrorDetails;
          const vals = new Set<string>(
            [
              known?.FRAG_PARSING_ERROR,
              known?.BUFFER_APPEND_ERROR,
              known?.BUFFER_APPENDING_ERROR,
              known?.FRAG_GAP,
            ]
              .filter(Boolean)
              .map((x) => String(x)),
          );
          if (vals.has(d)) return true;
          const dl = d.toLowerCase();
          return (
            dl.includes("demux") ||
            dl.includes("parsing") ||
            dl.includes("buffer_append") ||
            dl.includes("bufferappend") ||
            dl.includes("frag_gap") ||
            dl.includes("gap")
          );
        })();

        if (isDemuxLike) {
          const bump = () => {
            const cur = demuxRecoverRef.current;
            // отдельное окно, чтобы не крутиться бесконечно
            const WINDOW = 15000;
            if (!cur.windowStart || now - cur.windowStart > WINDOW) {
              demuxRecoverRef.current = { windowStart: now, attempts: 1 };
            } else {
              demuxRecoverRef.current = { windowStart: cur.windowStart, attempts: cur.attempts + 1 };
            }
            return demuxRecoverRef.current.attempts;
          };

          const attempt = bump();
          const max = 3;
          if (attempt <= max) {
            const backoff = 0.5;
            const pos = Math.max((video.currentTime || 0) - backoff, 0);
            console.warn(`[HLS] demux-like error -> reload around pos=${pos.toFixed(2)}s attempt=${attempt}/${max}`);
            try {
              hls.stopLoad();
            } catch {}
            try {
              if (attempt === max) {
                // крайний цикл: перезагружаем source, чтобы “сбросить” состояние демультиплексора
                hls.loadSource(hlsUrl);
              }
            } catch {}
            try {
              hls.startLoad(pos);
            } catch (e) {
              console.warn("[HLS] demux recovery startLoad failed:", e);
            }
            return;
          }
          // если исчерпали циклы демюкса — дальше работает общая логика fatal/recovery/fallback
        }

        if (seekModeRef.current) {
          if (now < seekQuietUntilRef.current) {
            // тихое окно после seeking: не считаем ошибки
            return;
          }

          // fatal в seekMode: сначала recovery (не уходим в MP4 мгновенно)
          if (fatal) {
            const ErrorTypes = (Hls as any).ErrorTypes;

            const bump = (ref: React.MutableRefObject<{ windowStart: number; attempts: number }>) => {
              const cur = ref.current;
              if (!cur.windowStart || now - cur.windowStart > FATAL_WINDOW_MS) {
                ref.current = { windowStart: now, attempts: 1 };
              } else {
                ref.current = { windowStart: cur.windowStart, attempts: cur.attempts + 1 };
              }
              return ref.current.attempts;
            };

            if (type === ErrorTypes?.NETWORK_ERROR) {
              const attempt = bump(fatalNetworkRef);
              if (attempt <= FATAL_RECOVERY_MAX_ATTEMPTS) {
                console.warn(`[HLS] seekMode fatal NETWORK_ERROR -> startLoad() attempt=${attempt}/${FATAL_RECOVERY_MAX_ATTEMPTS}`);
                try {
                  hls.startLoad();
                } catch (e) {
                  console.warn("[HLS] startLoad() failed:", e);
                }
                return;
              }
            } else if (type === ErrorTypes?.MEDIA_ERROR) {
              const attempt = bump(fatalMediaRef);
              if (attempt <= FATAL_RECOVERY_MAX_ATTEMPTS) {
                console.warn(
                  `[HLS] seekMode fatal MEDIA_ERROR -> recoverMediaError() attempt=${attempt}/${FATAL_RECOVERY_MAX_ATTEMPTS}`,
                );
                try {
                  hls.recoverMediaError();
                } catch (e) {
                  console.warn("[HLS] recoverMediaError() failed:", e);
                }
                return;
              }
            } else {
              // прочие fatal в seekMode: не фолбэчим мгновенно, но даём шанс восстановиться
              const attempt = bump(fatalOtherRef);
              console.warn(`[HLS] seekMode fatal OTHER -> attempt=${attempt}/${FATAL_OTHER_MAX_ATTEMPTS}`);
              if (attempt < FATAL_OTHER_MAX_ATTEMPTS) {
                try {
                  hls.startLoad();
                } catch {}
                return;
              }
            }
            // В seekMode fallback разрешён только через существующее правило timeout+no-progress (ниже).
          }

          // Если байты реально росли — это не «no-progress», даже если прилетел timeout
          if (details === fragTimeoutDetails && bytesProgressRecent) {
            console.warn("[HLS] seek frag timeout, but bytes are progressing -> skip fail count");
            return;
          }

          if (details === fragTimeoutDetails) {
            seekFailsRef.current += 1;
            console.warn(`[HLS] seek frag timeout count=${seekFailsRef.current}`);
          }

          // Правило 2: fallback в seek только если одновременно N таймаутов и давно нет прогресса по буферу
          const noProgressForMs = now - (seekLastProgressAtRef.current || 0);
          const hasRecentProgress = noProgressForMs < SEEK_NO_PROGRESS_MS;

          if (seekFailsRef.current >= SEEK_FAILS_BEFORE_FALLBACK && !hasRecentProgress) {
            console.error(
              `[HLS] seek fallback to MP4 reason=timeout+no-progress fails=${seekFailsRef.current} noProgressMs=${noProgressForMs}`,
            );
            destroyed = true;
            exitSeekMode("FALLBACK");
            fallbackToMp4();
          }
          return;
        }

        if (fatal) {
          // Не фолбэчим на MP4 по timeout, если загрузка фрагмента реально шла (байты росли недавно)
          if (details === fragTimeoutDetails && bytesProgressRecent) {
            console.warn("[HLS] Fatal FRAG_LOAD_TIMEOUT, but bytes are progressing -> skip MP4 fallback");
            return;
          }

          // Главное изменение №2: сначала recovery, потом fallback (anti-flap)
          const ErrorTypes = (Hls as any).ErrorTypes;

          const bump = (ref: React.MutableRefObject<{ windowStart: number; attempts: number }>) => {
            const cur = ref.current;
            if (!cur.windowStart || now - cur.windowStart > FATAL_WINDOW_MS) {
              ref.current = { windowStart: now, attempts: 1 };
            } else {
              ref.current = { windowStart: cur.windowStart, attempts: cur.attempts + 1 };
            }
            return ref.current.attempts;
          };

          if (type === ErrorTypes?.NETWORK_ERROR) {
            const attempt = bump(fatalNetworkRef);
            if (attempt <= FATAL_RECOVERY_MAX_ATTEMPTS) {
              console.warn(`[HLS] Fatal NETWORK_ERROR -> startLoad() attempt=${attempt}/${FATAL_RECOVERY_MAX_ATTEMPTS}`);
              try {
                hls.startLoad();
                return;
              } catch (e) {
                console.warn("[HLS] startLoad() failed:", e);
                // fallthrough
              }
            }
          } else if (type === ErrorTypes?.MEDIA_ERROR) {
            const attempt = bump(fatalMediaRef);
            if (attempt <= FATAL_RECOVERY_MAX_ATTEMPTS) {
              console.warn(
                `[HLS] Fatal MEDIA_ERROR -> recoverMediaError() attempt=${attempt}/${FATAL_RECOVERY_MAX_ATTEMPTS}`,
              );
              try {
                hls.recoverMediaError();
                return;
              } catch (e) {
                console.warn("[HLS] recoverMediaError() failed:", e);
                // fallthrough
              }
            }
          } else {
            const attempt = bump(fatalOtherRef);
            console.warn(`[HLS] Fatal OTHER -> attempt=${attempt}/${FATAL_OTHER_MAX_ATTEMPTS}`);
            if (attempt < FATAL_OTHER_MAX_ATTEMPTS) {
              // пробуем “мягко” перезапустить загрузку один раз вместо мгновенного fallback
              try {
                hls.startLoad();
                return;
              } catch {
                // fallthrough
              }
            }
          }

          // Если recovery “вычерпали” в окне — fallback на MP4
          console.error("[HLS] Fatal error after recovery attempts -> fallback to MP4");
          destroyed = true;
          fallbackToMp4();
        }
      });

      hls.attachMedia(video);

      // Таймер “первого сегмента”: не делаем fallback, если виден прогресс (байты/буфер)
      const firstFragTimerTick = () => {
        if (destroyed || firstFragLoaded || seekModeRef.current) return;

        const now2 = Date.now();
        const bytesProgressRecent2 = now2 - (fragBytesLastAtRef.current || 0) < FIRST_FRAG_NO_PROGRESS_MS;
        const bufferedAhead2 = getBufferedAheadSeconds();
        const hasBufferProgress = bufferedAhead2 > 0.2;
        const inFlight = Boolean(fragBytesInFlightRef.current);

        if (bytesProgressRecent2 || hasBufferProgress || inFlight) {
          console.warn(
            `[HLS] First-frag timer fired, but progress detected (bytesRecent=${bytesProgressRecent2}, inFlight=${inFlight}, bufferedAhead=${bufferedAhead2.toFixed(
              2,
            )}s) -> keep waiting`,
          );
          // переустанавливаем таймер и ждём дальше, без fallback
          clearFallbackTimer();
          fallbackTimerRef.current = window.setTimeout(firstFragTimerTick, FIRST_FRAG_TIMEOUT_MS);
          return;
        }

        // Нет признаков прогресса: делаем recovery-цикл, а не MP4 fallback
        const WINDOW = 120000; // окно подсчёта попыток на старт
        const cur = firstFragRecoverRef.current;
        const attempts =
          !cur.windowStart || now2 - cur.windowStart > WINDOW
            ? 1
            : Math.min(cur.attempts + 1, FIRST_FRAG_RECOVERY_MAX_CYCLES + 1);
        firstFragRecoverRef.current = { windowStart: !cur.windowStart || now2 - cur.windowStart > WINDOW ? now2 : cur.windowStart, attempts };

        if (attempts <= FIRST_FRAG_RECOVERY_MAX_CYCLES) {
          console.warn(`[HLS] First-frag no progress -> recovery cycle ${attempts}/${FIRST_FRAG_RECOVERY_MAX_CYCLES}`);
          try {
            hls.stopLoad();
          } catch {}
          try {
            hls.startLoad(0);
          } catch (e) {
            console.warn("[HLS] First-frag recovery startLoad failed:", e);
          }
          clearFallbackTimer();
          fallbackTimerRef.current = window.setTimeout(firstFragTimerTick, FIRST_FRAG_TIMEOUT_MS);
          return;
        }

        console.error(
          `[HLS] First-frag recovery exhausted (${attempts - 1} cycles) -> fallback to MP4`,
        );
        destroyed = true;
        fallbackToMp4();
      };

      fallbackTimerRef.current = window.setTimeout(firstFragTimerTick, FIRST_FRAG_TIMEOUT_MS);

      return () => {
        destroyed = true;
        clearFallbackTimer();
        clearSeekGraceTimer();
        video.removeEventListener("seeking", onVideoSeeking);
        video.removeEventListener("playing", onVideoPlaying);
        try {
          hls.destroy();
        } catch {}
        hlsRef.current = null;
      };
    } else {
      // Safari/iOS (или реально нативный HLS): включаем только если это Safari (а не Chrome "maybe")
      // ВАЖНО: добавляем таймаут на начало воспроизведения!
      if (isProbablySafari() && video.canPlayType("application/vnd.apple.mpegurl")) {
        console.log("[Video] Native HLS (Safari):", hlsUrl);
        video.src = hlsUrl;
        video.load();

        fallbackTimerRef.current = window.setTimeout(() => {
          if (!playbackStartedRef.current) {
            console.error(
              `[HLS] Native HLS timeout - no playback in ${NATIVE_HLS_PLAYBACK_TIMEOUT}s, falling back to MP4`,
            );
            fallbackToMp4();
          }
        }, NATIVE_HLS_PLAYBACK_TIMEOUT * 1000);

        return;
      }

      console.log("[HLS] hls.js not supported, using MP4");
      fallbackToMp4();
    }
  }, [hlsUrl, useMp4Fallback, preferHls, srcMp4, autoPlay, isLoading, fallbackToMp4, clearFallbackTimer, clearSeekGraceTimer, clearSeekMonitorTimer]);

  // Cleanup при unmount
  useEffect(() => {
    return () => {
      clearFallbackTimer();
      clearSeekGraceTimer();
      clearSeekMonitorTimer();
    };
  }, [clearFallbackTimer, clearSeekGraceTimer, clearSeekMonitorTimer]);

  // Проверка на внешние хосты
  try {
    const u = new URL(srcMp4);
    if (externalHosts.some((host) => u.hostname.includes(host))) {
      return (
        <div className={className}>
          <iframe src={mp4PlaybackUrl} width="100%" height="100%" allowFullScreen />
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

    // Главное изменение №4:
    // video.onerror для HLS часто “шумный” и не должен инициировать fallback.
    // Источник истины для ошибок HLS — Hls.Events.ERROR (для hls.js). Здесь только логируем.
    console.log("[Video] onError: no fallback (HLS ошибки обрабатываются в hls.js handler)");
    // Для MP4: если ошибка на старте, попробуем запустить server-side ensure-faststart
    maybeRequestFaststart("error", 0);
  }, [maybeRequestFaststart]);

  // Обработчик начала воспроизведения - отменяем таймаут
  const handlePlaying = useCallback(() => {
    console.log("[Video] Playback started");
    playbackStartedRef.current = true;

    // Если MP4 смог стартовать — считаем файл “рабочим” и больше не пытаемся чинить faststart автоматически.
    mp4OkRef.current.add(mp4Key);
    markMp4Ok(mp4Key);

    clearFallbackTimer();
    clearFaststartProbeTimer();
    clearFaststartPollTimer();
    clearFaststartStartupTimer();
    setFaststartUi({ phase: "idle" });
  }, [clearFallbackTimer, mp4Key]);

  // Обработчик timeupdate - тоже означает что воспроизведение идёт
  const handleTimeUpdate = useCallback(() => {
    if (!playbackStartedRef.current) {
      playbackStartedRef.current = true;

      mp4OkRef.current.add(mp4Key);
      markMp4Ok(mp4Key);

      clearFallbackTimer();
      clearFaststartProbeTimer();
      clearFaststartPollTimer();
      clearFaststartStartupTimer();
      setFaststartUi({ phase: "idle" });
    }
  }, [clearFallbackTimer, mp4Key]);

  // Обработчик stalled - быстрый fallback для HLS
  const handleStalled = useCallback(() => {
    console.warn("[Video] Playback stalled");

    // Главное изменение №4:
    // stalled/waiting не должны инициировать fallback (слишком “шумные” события),
    // только логируем. Ошибки/восстановление — через Hls.Events.ERROR.
    maybeRequestFaststart("stalled");
  }, [maybeRequestFaststart]);

  const handleWaiting = useCallback(() => {
    console.log("[Video] Waiting for data...");
    maybeRequestFaststart("waiting");
  }, [maybeRequestFaststart]);

  const handleLoadedMetadata = useCallback(() => {
    console.log("[Video] Metadata loaded");
  }, []);

  const handleCanPlay = useCallback(() => {
    console.log("[Video] Can play");
  }, []);

  return (
    <div>
      <video
        ref={videoRef}
        className={className}
        poster={poster}
        controls={controls}
        loop={loop}
        muted={muted}
        playsInline
        // Для MP4 даём браузеру начать streaming заранее (через Range); для HLS оставляем metadata.
        preload={useMp4Fallback ? "auto" : "metadata"}
        onError={handleVideoError}
        onPlaying={handlePlaying}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onStalled={handleStalled}
        onWaiting={handleWaiting}
        onCanPlay={handleCanPlay}
      />

      {faststartUi.phase !== "idle" && (
        <div style={{ marginTop: 12, display: "flex", gap: 12, alignItems: "center" }}>
          <Loader />
          <div style={{ fontSize: 14, lineHeight: 1.35 }}>
            <div style={{ fontWeight: 600 }}>Исправляем воспроизведение</div>
            <div>{faststartUi.message}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HlsVideo;
