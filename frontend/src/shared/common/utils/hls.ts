//import { CDN_ORIGIN } from "../helpers/commonConstants.ts";

/** SHA-1 для fallback слуга (как на бэке) */
async function sha1Hex(input: string): Promise<string> {
  const enc = new TextEncoder().encode(input);
  const buf = await crypto.subtle.digest("SHA-1", enc);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Слаг как на бэке: NFKD → ASCII → [-] → lower → max 60, пусто => sha1 */
export async function slugForHls(stem: string): Promise<string> {
  const nfkd = stem.normalize("NFKD");
  const noDiacritics = nfkd.replace(/[\u0300-\u036f]/g, "");
  const asciiOnly = noDiacritics.replace(/[^\x00-\x7F]/g, "");
  const dashed = asciiOnly
    .replace(/[^A-Za-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  if (dashed.length > 0) return dashed.slice(0, 60);
  const hex = await sha1Hex(stem);
  return hex.slice(0, 60);
}

/** 
 * Стабильный слаг (как stable_slug на бэке): 
 * truncate до 60 + короткий sha1-хвост для длинных имён 
 */
async function stableSlugForHls(stem: string): Promise<string> {
  const nfkd = stem.normalize("NFKD");
  const noDiacritics = nfkd.replace(/[\u0300-\u036f]/g, "");
  const asciiOnly = noDiacritics.replace(/[^\x00-\x7F]/g, "");
  const base = asciiOnly
    .replace(/[^A-Za-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  
  if (!base) {
    const hex = await sha1Hex(stem);
    return hex.slice(0, 60);
  }
  
  if (base.length <= 60) return base;
  
  // Для длинных имён добавляем sha1-хвост как на бэке
  const suffix = (await sha1Hex(stem)).slice(0, 8);
  const keep = 60 - 1 - suffix.length; // место под "-{suffix}"
  return `${base.slice(0, keep)}-${suffix}`;
}

/** Кандидаты путей к m3u8 из mp4-URL с учётом нарезок */
async function candidatesForPlaylist(mp4Url: string): Promise<string[] | null> {
  let u: URL;
  try {
    u = new URL(mp4Url);
  } catch {
    return null;
  }

  const baseOrigin = u.origin;
  const pathnameDecoded = decodeURIComponent(u.pathname); // ключи у вас юникод
  if (!pathnameDecoded.toLowerCase().endsWith(".mp4")) return null;

  const parts = pathnameDecoded.split("/").filter(Boolean);
  const file = parts.pop()!;
  const stem = file.replace(/\.mp4$/i, "");

  const basePath = parts.map(encodeURIComponent).join("/");

  // Генерируем все возможные слуги
  const slugCandidates: string[] = [];

  // slug #1 — legacy (как есть, max 60)
  const slug1 = await slugForHls(stem);
  slugCandidates.push(slug1);

  // slug #2 — stable (с sha1-хвостом для длинных имён)
  const slug2 = await stableSlugForHls(stem);
  if (slug2 !== slug1) slugCandidates.push(slug2);

  // slug #3 — для нарезок: отрежем хвост "_clip_<uuid-hex>"
  const stem3 = stem.replace(/_clip_[0-9a-f]{32}$/i, "");
  if (stem3 !== stem) {
    const slug3a = await slugForHls(stem3);
    const slug3b = await stableSlugForHls(stem3);
    slugCandidates.push(slug3a);
    if (slug3b !== slug3a) slugCandidates.push(slug3b);
  }

  // slug #4 — агрессивный: только a-z0-9 (помогает при нестандартных символах)
  const onlyAZ = stem
    .replace(/[^A-Za-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  if (onlyAZ && onlyAZ !== slug1) {
    const slug4 = await slugForHls(onlyAZ);
    if (!slugCandidates.includes(slug4)) slugCandidates.push(slug4);
  }

  const uniq = Array.from(
    new Set(
      slugCandidates
        .filter(Boolean)
        // Важно: origin берём из mp4Url (например media.dent-s.com), чтобы HLS плейлист/сегменты шли с того же хоста.
        .map((s) => `${baseOrigin}/${basePath}/.hls/${s}/playlist.m3u8`),
    ),
  );
  return uniq;
}

/** 
 * Проверка, что URL действительно HLS-плейлист 
 * С retry логикой для обработки временных ошибок CDN
 */
async function probePlaylist(url: string, retries: number = 3): Promise<boolean> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
      
      const res = await fetch(url, {
        method: "GET",
        mode: "cors",
        credentials: "omit",
        cache: "no-store",
        signal: controller.signal,
      });
      
      clearTimeout(timeoutId);

      // Ошибки CDN которые можно retry
      const retryableStatuses = [520, 521, 522, 523, 524, 502, 503, 504];
      if (retryableStatuses.includes(res.status) && attempt < retries) {
        console.warn(`[HLS] CDN error ${res.status} for ${url}, retry ${attempt + 1}/${retries}`);
        await new Promise(r => setTimeout(r, 1000 * (attempt + 1))); // Backoff
        continue;
      }

      if (!res.ok) {
        console.log(`[HLS] Probe failed for ${url}: HTTP ${res.status}`);
        return false;
      }

      const ct = (res.headers.get("content-type") || "").toLowerCase();
      // Принимаем разные варианты content-type для HLS
      const validContentTypes = ["mpegurl", "x-mpegurl", "vnd.apple", "application/octet-stream"];
      const hasValidContentType = validContentTypes.some(t => ct.includes(t));
      
      // Если content-type не HLS - проверяем содержимое
      const text = await res.text();
      
      if (!text.trimStart().startsWith("#EXTM3U")) {
        console.log(`[HLS] Invalid playlist (no #EXTM3U) for ${url}`);
        return false;
      }

      // Если content-type неправильный но содержимое валидное - логируем предупреждение
      if (!hasValidContentType) {
        console.warn(`[HLS] Unexpected content-type "${ct}" for ${url}, but content is valid HLS`);
      }

      // ⚡️ Валидация плейлиста
      const isMasterPlaylist = text.includes("#EXT-X-STREAM-INF:");
      const hasSegments = /#EXTINF:\s*[\d.]+/.test(text);
      const hasEndlist = text.includes("#EXT-X-ENDLIST");
      
      // Master playlist или Media playlist с сегментами
      if (isMasterPlaylist || hasSegments) {
        console.log(`[HLS] Valid playlist found: ${url} (master: ${isMasterPlaylist}, segments: ${hasSegments}, endlist: ${hasEndlist})`);
        return true;
      }

      // Плейлист-alias (ссылается на другой плейлист)
      const lines = text.split("\n").filter(l => l.trim() && !l.trim().startsWith("#"));
      const hasM3u8Link = lines.some(l => l.trim().endsWith(".m3u8"));
      if (hasM3u8Link) {
        console.log(`[HLS] Alias playlist found: ${url}`);
        return true;
      }

      console.log(`[HLS] Invalid playlist structure for ${url}`);
      return false;
    } catch (err) {
      // Сетевая ошибка или таймаут - пробуем retry
      if (attempt < retries) {
        console.warn(`[HLS] Network error for ${url}, retry ${attempt + 1}/${retries}:`, err);
        await new Promise(r => setTimeout(r, 1000 * (attempt + 1)));
        continue;
      }
      console.error(`[HLS] Final probe error for ${url}:`, err);
      return false;
    }
  }
  return false;
}

/** Резолв реального m3u8 (или null) */
export async function resolveHlsUrl(mp4Url: string): Promise<string | null> {
  const cands = await candidatesForPlaylist(mp4Url);
  if (!cands) return null;

  // Пробуем все кандидаты параллельно для ускорения
  const results = await Promise.all(
    cands.map(async (u) => {
      const ok = await probePlaylist(u);
      return ok ? u : null;
    })
  );

  // Возвращаем первый успешный
  for (const r of results) {
    if (r) return r;
  }
  
  return null;
}
