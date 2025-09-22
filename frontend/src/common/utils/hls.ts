export const CDN_ORIGIN = "https://cdn.dent-s.com";

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

/** Кандидаты путей к m3u8 из mp4-URL с учётом нарезок */
async function candidatesForPlaylist(mp4Url: string): Promise<string[] | null> {
  let u: URL;
  try {
    u = new URL(mp4Url);
  } catch {
    return null;
  }

  const pathnameDecoded = decodeURIComponent(u.pathname); // ключи у вас юникод
  if (!pathnameDecoded.toLowerCase().endsWith(".mp4")) return null;

  const parts = pathnameDecoded.split("/").filter(Boolean);
  const file = parts.pop()!;
  const stem = file.replace(/\.mp4$/i, "");

  const basePath = parts.map(encodeURIComponent).join("/");

  // slug #1 — как есть
  const slug1 = await slugForHls(stem);

  // slug #2 — для нарезок: отрежем хвост "_clip_<uuid-hex>"
  // clip_tasks создаёт .../<stem>_clip_<uuid.hex>.mp4
  const stem2 = stem.replace(/_clip_[0-9a-f]{32}$/i, "");
  const slug2 = stem2 !== stem ? await slugForHls(stem2) : null;

  // slug #3 — агрессивный: только a-z0-9 (помогает при нестандартных символах)
  const onlyAZ = stem
    .replace(/[^A-Za-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  const slug3 = await slugForHls(onlyAZ);

  const uniq = Array.from(
    new Set(
      [slug1, slug2, slug3]
        .filter(Boolean)
        .map((s) => `${CDN_ORIGIN}/${basePath}/.hls/${s}/playlist.m3u8`),
    ),
  );
  return uniq;
}

/** Проверка, что URL действительно HLS-плейлист */
async function probePlaylist(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, {
      method: "GET",
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
    });
    if (!res.ok) return false;

    const ct = (res.headers.get("content-type") || "").toLowerCase();
    if (!ct.includes("mpegurl")) return false;

    const text = await res.text();
    if (!text.trimStart().startsWith("#EXTM3U")) return false;

    // ⚡️ Доп. проверка: есть ли сегменты > 0
    const hasSegments = /#EXTINF:\s*(?!0(\.0+)?)/.test(text);
    return hasSegments;
  } catch {
    return false;
  }
}

/** Резолв реального m3u8 (или null) */
export async function resolveHlsUrl(mp4Url: string): Promise<string | null> {
  const cands = await candidatesForPlaylist(mp4Url);
  if (!cands) return null;

  // пробуем по очереди
  for (const u of cands) {
    if (await probePlaylist(u)) return u;
  }
  return null;
}
