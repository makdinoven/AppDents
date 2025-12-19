const HOST_ALLOWLIST = new Set(["cdn.dent-s.com"]);
const SEGMENT_INFLIGHT = new Map(); // cacheKey -> Promise<Response>

// MP4: режем Range на небольшие чанки, чтобы не стримить гигантский HTTP/2 поток (частая причина ERR_HTTP2_PROTOCOL_ERROR)
// Плюс: докачиваем чанк полностью на воркере (с ретраями) и отдаём клиенту уже готовый буфер.
const MAX_MP4_RANGE_BYTES = 2 * 1024 * 1024; // 2MB (больше запросов, но меньше вероятность HTTP/2 reset на одном чанке)

function clampMp4Range(rangeValue) {
  // ожидаем "bytes=start-" или "bytes=start-end"
  const m = /^bytes=(\d+)-(\d*)$/i.exec(rangeValue || "");
  if (!m) return null;
  const start = parseInt(m[1], 10);
  if (!Number.isFinite(start) || start < 0) return null;
  const endStr = m[2];
  const requestedEnd = endStr ? parseInt(endStr, 10) : null;
  const cappedEnd =
    requestedEnd != null && Number.isFinite(requestedEnd)
      ? Math.min(requestedEnd, start + MAX_MP4_RANGE_BYTES - 1)
      : start + MAX_MP4_RANGE_BYTES - 1;
  return `bytes=${start}-${cappedEnd}`;
}

function parseRange(rangeValue) {
  const m = /^bytes=(\d+)-(\d*)$/i.exec(rangeValue || "");
  if (!m) return null;
  const start = parseInt(m[1], 10);
  if (!Number.isFinite(start) || start < 0) return null;
  const end = m[2] ? parseInt(m[2], 10) : null;
  return { start, end: end != null && Number.isFinite(end) ? end : null };
}

async function fetchWithTimeout(url, init, timeoutMs) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(new Error("fetch timeout")), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
}

async function serveMp4Range({ request, originUrl, cf, rangeHeader, slicedRangeHeader, h }) {
  // ВАЖНО: не стримим body напрямую — докачиваем на воркере, чтобы не отдавать “полубайт” клиенту при reset.
  const maxAttempts = 10;
  const attemptTimeoutMs = 30000;
  let lastErr = null;

  const parsed = parseRange(slicedRangeHeader);
  const expectedLen =
    parsed && parsed.end != null && parsed.end >= parsed.start ? parsed.end - parsed.start + 1 : null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const originResp = await fetchWithTimeout(originUrl, {
        method: "GET",
        headers: h,
        redirect: "follow",
        cf,
      }, attemptTimeoutMs);

      // ожидаем 206 (или 200 если origin игнорирует Range)
      if (!(originResp.status === 206 || originResp.status === 200)) {
        const errHeaders = withNoStorePlainText(new Headers());
        errHeaders.set("x-worker", "cdn-split-v15");
        errHeaders.set("x-worker-origin-status", String(originResp.status));
        errHeaders.set("x-worker-range", String(rangeHeader || ""));
        errHeaders.set("x-worker-sliced-range", String(slicedRangeHeader || ""));
        errHeaders.set("x-worker-attempt", String(attempt));
        for (const [k, v] of corsHeaders()) errHeaders.set(k, v);
        return new Response(`Origin returned ${originResp.status}`, { status: 502, headers: errHeaders });
      }

      let buf;
      try {
        buf = await originResp.arrayBuffer();
      } catch (e) {
        throw new Error(`arrayBuffer failed: ${safeErr(e)}`);
      }
      if (!buf || buf.byteLength === 0) {
        throw new Error("empty mp4 range payload");
      }
      if (expectedLen != null && buf.byteLength !== expectedLen) {
        throw new Error(`mp4 range truncated expected=${expectedLen} got=${buf.byteLength}`);
      }

      const headers = new Headers(originResp.headers);
      headers.set("x-worker", "cdn-split-v15");
      headers.set("x-worker-origin-status", String(originResp.status));
      headers.set("x-worker-range", String(rangeHeader || ""));
      headers.set("x-worker-sliced-range", String(slicedRangeHeader || ""));
      headers.set("x-worker-attempt", String(attempt));
      if (expectedLen != null) headers.set("x-worker-expected-len", String(expectedLen));
      headers.set("X-Content-Type-Options", "nosniff");
      headers.set("Cache-Control", "no-store");
      for (const [k, v] of corsHeaders()) headers.set(k, v);

      // Стандартизируем длину (важно для браузера)
      headers.set("Content-Length", String(buf.byteLength));
      headers.delete("Transfer-Encoding");

      // Если origin игнорировал Range и вернул 200/full — всё равно отдаём 206 с нашим диапазоном
      if (originResp.status !== 206) {
        // Если знаем end — формируем Content-Range сами. Если не знаем — оставляем то, что пришло.
        if (parsed && parsed.end != null) {
          // total может быть в origin headers (content-range); если нет — не подставляем.
          const cr = headers.get("content-range");
          const total = cr && /\/\d+$/i.test(cr) ? cr.split("/").pop() : null;
          if (total) {
            headers.set("Content-Range", `bytes ${parsed.start}-${parsed.end}/${total}`);
          } else {
            headers.set("Content-Range", `bytes ${parsed.start}-${parsed.end}/*`);
          }
        }
        headers.set("Accept-Ranges", "bytes");
      }

      return new Response(buf, { status: 206, headers });
    } catch (e) {
      lastErr = e;
      if (attempt < maxAttempts) {
        await sleep(backoffMsJitter(attempt));
        continue;
      }
    }
  }

  const errHeaders = withNoStorePlainText(new Headers());
  errHeaders.set("x-worker", "cdn-split-v15");
  errHeaders.set("x-worker-error", safeErr(lastErr));
  errHeaders.set("x-worker-range", String(rangeHeader || ""));
  errHeaders.set("x-worker-sliced-range", String(slicedRangeHeader || ""));
  errHeaders.set("x-worker-expected-len", String(expectedLen ?? ""));
  for (const [k, v] of corsHeaders()) errHeaders.set(k, v);
  return new Response("MP4 range fetch failed", { status: 502, headers: errHeaders });
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const host = url.hostname;
    const path = url.pathname;
    const p = path.toLowerCase();
    const cdnOrigin = url.origin; // https://cdn.dent-s.com
    if (!HOST_ALLOWLIST.has(host)) return fetch(request);

    try {
      if (request.method === "OPTIONS") {
        return new Response(null, { status: 204, headers: corsHeaders() });
      }

      const ORIGIN_BASE =
        "https://s3.twcstorage.ru/604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254";

      const isPlaylist = p.endsWith(".m3u8") || p.endsWith(".m3u");
      const isSegment = p.endsWith(".ts") || p.endsWith(".m4s") || p.endsWith(".aac");

      const isMp4 = p.endsWith(".mp4") || p.endsWith(".mov");

      const isImage =
        p.endsWith(".webp") || p.endsWith(".jpg") || p.endsWith(".jpeg") ||
        p.endsWith(".png")  || p.endsWith(".svg") || p.endsWith(".gif")  || p.endsWith(".avif");

      const isPdf = p.endsWith(".pdf");

      // --- sanitize query ---
      // segments: drop ALL query
      // others: drop only r
      const sanitizedSearch = sanitizeSearch(url.searchParams, {
        dropAll: isSegment,
        dropKeys: ["r"],
      });

      const originUrl = ORIGIN_BASE + path + sanitizedSearch;

      // --- headers to origin ---
      const h = new Headers();
      copyIfPresent(request.headers, h, "if-none-match");
      copyIfPresent(request.headers, h, "if-modified-since");
      copyIfPresent(request.headers, h, "origin");
      copyIfPresent(request.headers, h, "referer");
      copyIfPresent(request.headers, h, "user-agent");

      // Range only for mp4
      const clientHasRange = request.headers.has("range");
      const clientRangeValue = clientHasRange ? request.headers.get("range") : null;
      const mp4SlicedRange = isMp4 && clientHasRange && clientRangeValue ? clampMp4Range(clientRangeValue) : null;
      if (mp4SlicedRange) h.set("range", mp4SlicedRange);

      // --- cacheKey ---
      // segments: origin+path only
      // others: origin+path+sanitizedSearch (r removed)
      const cacheKey = isSegment ? `${url.origin}${path}` : `${url.origin}${path}${sanitizedSearch}`;

      // --- CF cache hints ---
      // IMPORTANT: do NOT use cacheEverything for images (чтобы не закэшировать HTML/404 как jpg)
      let cf = { cacheEverything: false };
      if (isPdf) cf = { cacheEverything: true, cacheTtl: 86400 };
      else if (isPlaylist) cf = { cacheEverything: true, cacheTtl: 10, cacheKey };
      else if (isSegment) cf = { cacheEverything: true, cacheTtl: 31536000, cacheKey };

      // =========================
      // SEGMENTS: cache-first + buffer + put
      // =========================
      
      if (isSegment) {
        return serveSegment({ ctx, originUrl, cf, cacheKey, path, p, h, cdnOrigin });
      }

      // =========================
      // IMAGES: cache-first + stale-if-error + validate
      // =========================
      if (isImage) {
        return serveImage({ ctx, originUrl, cf, cacheKey, path, p, h });
      }

      // MP4: если пришёл Range — обслуживаем через буферизацию чанка на воркере (анти HTTP/2 reset)
      if (isMp4 && clientHasRange && clientRangeValue && mp4SlicedRange) {
        return serveMp4Range({
          request,
          originUrl,
          cf,
          rangeHeader: clientRangeValue,
          slicedRangeHeader: mp4SlicedRange,
          h,
        });
      }

      // =========================
      // PLAYLIST / OTHER: stream
      // =========================
      const originResp = await fetchWithRetry(originUrl, {
        method: request.method,
        headers: h,
        redirect: "follow",
        cf,
      }, isPlaylist ? 4 : 2);

      const headers = new Headers(originResp.headers);
      headers.set("x-worker", "cdn-split-v15");
      headers.set("x-worker-origin-status", String(originResp.status));
      headers.set("Vary", appendVary(headers.get("Vary"), "Origin"));
      for (const [k, v] of corsHeaders()) headers.set(k, v);

      if (isPlaylist) {
        if (!originResp.ok) {
          const errHeaders = withNoStorePlainText(headers);
          return new Response(
            originResp.status >= 500 ? "Origin 5xx while fetching playlist" :
            originResp.status === 404 ? "Playlist not found" :
            `Origin returned ${originResp.status}`,
            { status: originResp.status >= 500 ? 502 : originResp.status, headers: errHeaders }
          );
        }
        headers.set("Content-Type", "application/vnd.apple.mpegurl; charset=utf-8");
        headers.set("Cache-Control", "public, max-age=10, stale-while-revalidate=30");
        headers.delete("Content-Range");
        headers.delete("Content-Length");
        headers.set("X-Content-Type-Options", "nosniff");
        return new Response(originResp.body, { status: 200, headers });
      }

      if (isPdf) headers.set("Cache-Control", "public, max-age=86400, stale-while-revalidate=86400");
      else if (isMp4 && clientHasRange) headers.set("Cache-Control", "no-store");
      else if (isMp4) headers.set("Cache-Control", "public, max-age=3600");
      else headers.set("Cache-Control", "public, max-age=300");

      headers.set("X-Content-Type-Options", "nosniff");
      return new Response(originResp.body, { status: originResp.status, statusText: originResp.statusText, headers });

    } catch (err) {
      const h = new Headers();
      for (const [k, v] of corsHeaders()) h.set(k, v);
      h.set("Content-Type", "text/plain; charset=utf-8");
      h.set("Cache-Control", "no-store");
      h.set("x-worker", "cdn-split-v15");
      h.set("x-worker-error", safeErr(err));
      return new Response("Worker error", { status: 500, headers: h });
    }
  },
};

// ---------- сегменты ----------
async function serveSegment({ ctx, originUrl, cf, cacheKey, path, p, h, cdnOrigin }) {
  const edgeCache = caches.default;
  const keyReq = new Request(cacheKey, { method: "GET" });

  const wrapCached = (cached, extra = {}) => {
    const outHeaders = new Headers(cached.headers);
    outHeaders.set("x-worker", "cdn-split-v15");
    outHeaders.set("X-Content-Type-Options", "nosniff");
    for (const [k, v] of corsHeaders()) outHeaders.set(k, v);
    for (const [k, v] of Object.entries(extra)) outHeaders.set(k, String(v));
    return new Response(cached.body, { status: cached.status, headers: outHeaders });
  };

  // 1) cache-first
  const cached = await edgeCache.match(keyReq);
  if (cached) return wrapCached(cached, { "x-edge-cache": "HIT" });

  // 2) single-flight: если уже качаем этот сегмент — ждём тот же Promise
  const inflight = SEGMENT_INFLIGHT.get(cacheKey);
  if (inflight) {
    try {
      const resp = await inflight;
      // на всякий случай ещё раз попробуем cache (может уже положили)
      const cached2 = await edgeCache.match(keyReq);
      if (cached2) return wrapCached(cached2, { "x-edge-cache": "STALE" });
      return resp;
    } catch {
      // fallthrough в свой fetch
    }
  }

  const pFetch = (async () => {
    const maxAttempts = 5;
    let lastErr = null;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      // перед попыткой — вдруг другой воркер уже успел положить
      const maybeCached = await edgeCache.match(keyReq);
      if (maybeCached) return wrapCached(maybeCached, { "x-edge-cache": "STALE" });

      try {
        const originResp = await fetch(originUrl, {
          method: "GET",
          headers: h,
          redirect: "follow",
          cf,
        });

        if (!originResp.ok) {
          const errHeaders = withNoStorePlainText(new Headers());
          errHeaders.set("x-worker", "cdn-split-v15");
          errHeaders.set("x-edge-cache", "MISS");
          errHeaders.set("x-worker-origin-status", String(originResp.status));
          errHeaders.set("x-worker-attempt", String(attempt));
          for (const [k, v] of corsHeaders()) errHeaders.set(k, v);

          const status = originResp.status >= 500 ? 502 : originResp.status;
          return new Response(
            originResp.status >= 500
              ? "Origin 5xx while fetching segment"
              : originResp.status === 404
                ? "Segment not found"
                : `Origin returned ${originResp.status}`,
            { status, headers: errHeaders },
          );
        }

        let buf;
        try {
          buf = await originResp.arrayBuffer();
        } catch (e) {
          lastErr = e;
          const stale = await edgeCache.match(keyReq);
          if (stale) return wrapCached(stale, { "x-edge-cache": "STALE", "x-worker-error": safeErr(e) });
          if (attempt < maxAttempts) {
            await sleep(backoffMsJitter(attempt));
            continue;
          }
          throw e;
        }

        const ct = String(originResp.headers.get("content-type") || "").toLowerCase();
        if (!buf || buf.byteLength === 0 || ct.includes("text/") || ct.includes("application/json") || ct.includes("application/xml")) {
          const badHeaders = withNoStorePlainText(new Headers());
          badHeaders.set("x-worker", "cdn-split-v15");
          badHeaders.set("x-edge-cache", "MISS");
          badHeaders.set("x-worker-attempt", String(attempt));
          badHeaders.set("x-hls-origin-bad", `ct="${ct}" bytes=${buf ? buf.byteLength : 0}`);
          for (const [k, v] of corsHeaders()) badHeaders.set(k, v);
          return new Response("Bad HLS segment payload", { status: 502, headers: badHeaders });
        }

        const outHeaders = new Headers(originResp.headers);
        outHeaders.set("x-worker", "cdn-split-v15");
        outHeaders.set("x-edge-cache", "MISS");
        outHeaders.set("x-worker-attempt", String(attempt));
        outHeaders.set("X-Content-Type-Options", "nosniff");

        if (p.endsWith(".ts")) outHeaders.set("Content-Type", "video/mp2t");
        else if (p.endsWith(".aac")) outHeaders.set("Content-Type", "audio/aac");
        else if (p.endsWith(".m4s")) outHeaders.set("Content-Type", "video/iso.segment");

        outHeaders.set("Cache-Control", "public, max-age=31536000, immutable, stale-while-revalidate=86400");
        outHeaders.delete("Content-Length");
        outHeaders.delete("Transfer-Encoding");
        outHeaders.delete("Content-Range");
        for (const [k, v] of corsHeaders()) outHeaders.set(k, v);

        const resp = new Response(buf, { status: 200, headers: outHeaders });

        // кладём в cache в фоне
        ctx.waitUntil(edgeCache.put(keyReq, resp.clone()).catch(() => {}));

        ctx.waitUntil(
          prefetchNextSegments({
            ctx,
            edgeCache,
            originUrl,
            cf,
            h,
            path,
            cdnOrigin,
            count: 3,
            concurrency: 2,
          }),
        );

        return resp;
      } catch (e) {
        lastErr = e;
        const stale = await edgeCache.match(keyReq);
        if (stale) return wrapCached(stale, { "x-edge-cache": "STALE", "x-worker-error": safeErr(e) });
        if (attempt < maxAttempts) {
          await sleep(backoffMsJitter(attempt));
          continue;
        }
      }
    }

    const errHeaders = withNoStorePlainText(new Headers());
    errHeaders.set("x-worker", "cdn-split-v15");
    errHeaders.set("x-worker-error", safeErr(lastErr));
    for (const [k, v] of corsHeaders()) errHeaders.set(k, v);
    return new Response("Segment fetch failed", { status: 502, headers: errHeaders });
  })();

  SEGMENT_INFLIGHT.set(cacheKey, pFetch);

  try {
    return await pFetch;
  } finally {
    SEGMENT_INFLIGHT.delete(cacheKey);
  }
}

function backoffMsJitter(attempt) {
  const base = [300, 700, 1500, 2500, 4000][Math.min(attempt - 1, 4)];
  const jitter = base * (0.8 + Math.random() * 0.4);
  return Math.round(jitter);
}
// ---------- картинки ----------
async function serveImage({ ctx, originUrl, cf, cacheKey, path, p, h }) {
  const edgeCache = caches.default;

  // 1) cache-first
  const cached = await edgeCache.match(cacheKey);
  if (cached) {
    const outHeaders = new Headers(cached.headers);
    outHeaders.set("x-worker", "cdn-split-v15");
    outHeaders.set("x-edge-cache", "HIT");
    outHeaders.set("Cross-Origin-Resource-Policy", "cross-origin");
    outHeaders.set("X-Content-Type-Options", "nosniff");
    for (const [k, v] of corsHeaders()) outHeaders.set(k, v);

    // (опционально) тихо обновить кэш в фоне
    ctx.waitUntil(refreshImageCache({ edgeCache, cacheKey, originUrl, cf, path, p, h }));

    return new Response(cached.body, { status: cached.status, headers: outHeaders });
  }

  // 2) miss -> fetch with retries
  try {
    const resp = await fetchAndBuildImage({ originUrl, cf, path, p, h });
    // cache good
    ctx.waitUntil(edgeCache.put(cacheKey, resp.clone()));
    return resp;
  } catch (err) {
    // 3) если fetch упал (Network connection lost), но вдруг кэш появился — отдать stale
    const stale = await edgeCache.match(cacheKey);
    if (stale) {
      const outHeaders = new Headers(stale.headers);
      outHeaders.set("x-worker", "cdn-split-v15");
      outHeaders.set("x-edge-cache", "STALE");
      outHeaders.set("x-worker-error", safeErr(err));
      outHeaders.set("Cross-Origin-Resource-Policy", "cross-origin");
      outHeaders.set("X-Content-Type-Options", "nosniff");
      for (const [k, v] of corsHeaders()) outHeaders.set(k, v);
      return new Response(stale.body, { status: stale.status, headers: outHeaders });
    }

    // 4) если stale нет — честная ошибка (но no-store)
    const errHeaders = withNoStorePlainText(new Headers());
    errHeaders.set("x-worker", "cdn-split-v15");
    errHeaders.set("x-worker-error", safeErr(err));
    for (const [k, v] of corsHeaders()) errHeaders.set(k, v);
    return new Response("Image fetch failed", { status: 502, headers: errHeaders });
  }
}

async function refreshImageCache({ edgeCache, cacheKey, originUrl, cf, path, p, h }) {
  // попытка обновления (не критично если упадёт)
  try {
    const resp = await fetchAndBuildImage({ originUrl, cf, path, p, h });
    await edgeCache.put(cacheKey, resp.clone());
  } catch {
    // ignore
  }
}

async function fetchAndBuildImage({ originUrl, cf, path, p, h }) {
  const originResp = await fetchWithRetry(originUrl, {
    method: "GET",
    headers: h,
    redirect: "follow",
    cf, // cacheEverything:false
  }, 6);

  // не кэшируем ошибки
  if (!originResp.ok) {
    throw new Error(`origin status ${originResp.status}`);
  }

  const buf = await originResp.arrayBuffer();

  const headers = new Headers(originResp.headers);
  headers.set("x-worker", "cdn-split-v15");
  headers.set("x-edge-cache", "MISS");
  headers.set("Cross-Origin-Resource-Policy", "cross-origin");

  // Content-Type fix
  const forced = contentTypeFromPath(path);
  const current = String(headers.get("content-type") || "").toLowerCase();
  const looksGeneric =
    !current ||
    current.includes("application/octet-stream") ||
    current.includes("binary/octet-stream");

  if (forced && (looksGeneric || !current.startsWith("image/"))) {
    headers.set("Content-Type", forced);
  }

  const finalCt = String(headers.get("content-type") || "").toLowerCase();
  if (!finalCt.startsWith("image/") || !buf || buf.byteLength === 0) {
    throw new Error(`bad image payload ct="${finalCt}" bytes=${buf ? buf.byteLength : 0}`);
  }

  headers.set("X-Content-Type-Options", "nosniff");
  headers.set("Cache-Control", "public, max-age=604800, immutable, stale-while-revalidate=86400");
  headers.delete("Content-Length");
  headers.delete("Transfer-Encoding");

  for (const [k, v] of corsHeaders()) headers.set(k, v);

  return new Response(buf, { status: 200, headers });
}

// ---------- helpers ----------
function sanitizeSearch(searchParams, { dropAll = false, dropKeys = [] } = {}) {
  if (dropAll) return "";
  const sp = new URLSearchParams(searchParams);
  for (const k of dropKeys) sp.delete(k);
  const s = sp.toString();
  return s ? `?${s}` : "";
}

async function fetchWithRetry(url, init, attempts = 1) {
  let lastErr = null;
  for (let i = 1; i <= attempts; i++) {
    try {
      const resp = await fetch(url, init);
      if (resp.status >= 500 && i < attempts) {
        await sleep(backoffMs(i));
        continue;
      }
      return resp;
    } catch (e) {
      lastErr = e;
      if (i < attempts) {
        await sleep(backoffMs(i));
        continue;
      }
    }
  }
  throw lastErr || new Error("fetchWithRetry failed");
}

function contentTypeFromPath(path) {
  const p = path.toLowerCase();
  if (p.endsWith(".png")) return "image/png";
  if (p.endsWith(".jpg") || p.endsWith(".jpeg")) return "image/jpeg";
  if (p.endsWith(".webp")) return "image/webp";
  if (p.endsWith(".gif")) return "image/gif";
  if (p.endsWith(".svg")) return "image/svg+xml; charset=utf-8";
  if (p.endsWith(".avif")) return "image/avif";
  return null;
}

function backoffMs(attempt) {
  const base = 180 * Math.pow(2, attempt - 1);
  return Math.min(3000, base);
}
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function corsHeaders() {
  return new Map([
    ["Access-Control-Allow-Origin", "*"],
    ["Access-Control-Allow-Methods", "GET,HEAD,OPTIONS"],
    ["Access-Control-Allow-Headers", "Range,Content-Type,Origin,Accept"],
    [
      "Access-Control-Expose-Headers",
      [
        "Content-Length",
        "Content-Range",
        "Accept-Ranges",
        "X-Edge-Cache",
        "X-Worker",
        "X-Worker-Error",
        "X-Worker-Origin-Status",
        "X-Worker-Attempt",
        "X-Hls-Origin-Bad",
      ].join(", "),
    ],
  ]);
}

function appendVary(existing, add) {
  if (!existing) return add;
  const parts = existing.split(",").map(s => s.trim()).filter(Boolean);
  if (parts.some(x => x.toLowerCase() === add.toLowerCase())) return existing;
  return existing + ", " + add;
}

function copyIfPresent(srcHeaders, dstHeaders, name) {
  const v = srcHeaders.get(name);
  if (v) dstHeaders.set(name, v);
}

function withNoStorePlainText(headers) {
  const h = new Headers(headers);
  h.set("Content-Type", "text/plain; charset=utf-8");
  h.set("Cache-Control", "no-store");
  h.delete("Content-Length");
  h.delete("Transfer-Encoding");
  return h;
}

function safeErr(err) {
  try {
    if (!err) return "unknown";
    if (typeof err === "string") return err.slice(0, 180);
    const msg = (err && (err.message || err.toString())) || "unknown";
    return String(msg).slice(0, 180);
  } catch {
    return "unknown";
  }
}
async function prefetchNextSegments({
  ctx,
  edgeCache,
  originUrl,
  cf,
  h,
  path,
  cdnOrigin,
  count = 3,         // сколько сегментов вперёд
  concurrency = 2,   // сколько параллельно качать
}) {
  // Ожидаем .../segment_000.ts
  const m = /\/segment_(\d+)\.ts$/i.exec(path);
  if (!m) return;

  const curNumStr = m[1];
  const width = curNumStr.length;
  const curNum = parseInt(curNumStr, 10);
  if (!Number.isFinite(curNum)) return;

  const basePath = path.slice(0, path.lastIndexOf("/") + 1); // .../.hls/.../
  const originBase = originUrl.slice(0, originUrl.lastIndexOf("/") + 1);

  // простая очередь задач
  const tasks = [];
  for (let i = 1; i <= count; i++) {
    const n = String(curNum + i).padStart(width, "0");
    const nextPath = `${basePath}segment_${n}.ts`;

    // КЛЮЧ ДЛЯ EDGE CACHE — ДОЛЖЕН БЫТЬ CDN ORIGIN
    const nextCacheKey = `${cdnOrigin}${nextPath}`;
    const keyReq = new Request(nextCacheKey, { method: "GET" });

    tasks.push(async () => {
      // если уже есть — не качаем
      const cached = await edgeCache.match(keyReq);
      if (cached) return;

      // single-flight (и для префетча, и для обычной загрузки)
      if (SEGMENT_INFLIGHT.get(nextCacheKey)) return;

      const nextOriginUrl = `${originBase}segment_${n}.ts`;

      const pFetch = (async () => {
        const resp = await fetch(nextOriginUrl, { method: "GET", headers: h, redirect: "follow", cf });
        if (!resp.ok) return;

        const buf = await resp.arrayBuffer();
        if (!buf || buf.byteLength === 0) return;

        const outHeaders = new Headers(resp.headers);
        outHeaders.set("x-worker", "cdn-split-v15");
        outHeaders.set("x-edge-cache", "PREFETCH");
        outHeaders.set("X-Content-Type-Options", "nosniff");
        outHeaders.set("Content-Type", "video/mp2t");
        outHeaders.set("Cache-Control", "public, max-age=31536000, immutable, stale-while-revalidate=86400");
        outHeaders.delete("Content-Length");
        outHeaders.delete("Transfer-Encoding");
        outHeaders.delete("Content-Range");
        for (const [k, v] of corsHeaders()) outHeaders.set(k, v);

        const r = new Response(buf, { status: 200, headers: outHeaders });
        await edgeCache.put(keyReq, r);
      })();

      SEGMENT_INFLIGHT.set(nextCacheKey, pFetch);
      try {
        await pFetch;
      } finally {
        SEGMENT_INFLIGHT.delete(nextCacheKey);
      }
    });
  }

  // runner с ограничением параллельности
  let idx = 0;
  const workers = new Array(Math.max(1, concurrency)).fill(0).map(async () => {
    while (idx < tasks.length) {
      const my = idx++;
      try {
        await tasks[my]();
      } catch {
        // ignore: prefetch не должен ломать основной ответ
      }
    }
  });

  await Promise.all(workers);
}