// utils/hls.ts
export const CDN_ORIGIN = "https://cdn.dent-s.com";

/** SHA-1 (нужен для случайно пустых слугов — как в бэкенде) */
async function sha1Hex(input: string): Promise<string> {
  const enc = new TextEncoder().encode(input);
  const buf = await crypto.subtle.digest("SHA-1", enc);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Слаг в точности как на бэке: NFKD → ASCII → [^A-Za-z0-9]+ → '-' → lower → max 60; если пусто — sha1 */
export async function slugForHls(stem: string): Promise<string> {
  // 1) NFKD + удаление диакритики и не-ASCII
  const nfkd = stem.normalize("NFKD");
  const noDiacritics = nfkd.replace(/[\u0300-\u036f]/g, "");
  const asciiOnly = noDiacritics.replace(/[^\x00-\x7F]/g, "");
  // 2) в "-" и приведение
  const dashed = asciiOnly
    .replace(/[^A-Za-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toLowerCase();
  if (dashed.length > 0) return dashed.slice(0, 60);
  // 3) fallback как на бэке: sha1(stem) → первые 60 символов
  const hex = await sha1Hex(stem);
  return hex.slice(0, 60);
}

/** Из mp4-ссылки получить HLS playlist.m3u8 на CDN (возвращает null, если не mp4) */
export async function mp4ToHlsUrl(mp4Url: string): Promise<string | null> {
  let u: URL;
  try {
    u = new URL(mp4Url);
  } catch {
    return null;
  }
  const pathnameDecoded = decodeURIComponent(u.pathname); // имена в бакете у вас юникод — декодируем
  if (!pathnameDecoded.toLowerCase().endsWith(".mp4")) return null;

  const parts = pathnameDecoded.split("/").filter(Boolean);
  const file = parts.pop()!;
  const stem = file.replace(/\.mp4$/i, "");
  const slug = await slugForHls(stem);

  // базовый путь перекодируем по сегментам (пробелы, кириллица и т.д.)
  const basePath = parts.map(encodeURIComponent).join("/");
  const playlistPath = `${basePath}/.hls/${slug}/playlist.m3u8`;

  // всегда идём через CDN_ORIGIN (независимо от исходного хоста)
  return `${CDN_ORIGIN}/${playlistPath}`;
}
