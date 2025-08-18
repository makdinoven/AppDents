export function slugFromStem(stem: string): string {
  const ascii = stem.normalize("NFKD").replace(/[^\x00-\x7F]/g, "");
  const hyphen = ascii.replace(/[^A-Za-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return hyphen.toLowerCase().slice(0, 60);
}

export function buildHlsUrl(
  originalUrl: string,
  cdnHost = "https://cdn.dent-s.com",
): string | null {
  try {
    const url = new URL(originalUrl);
    const parts = url.pathname.split("/");
    const fileNameEncoded = parts.pop();
    if (!fileNameEncoded) return null;

    const fileName = decodeURIComponent(fileNameEncoded);
    const dotIndex = fileName.lastIndexOf(".");
    if (dotIndex < 0) return null;

    const ext = fileName.slice(dotIndex + 1).toLowerCase();
    if (ext !== "mp4") return null;

    const stem = fileName.slice(0, dotIndex);
    const slug = slugFromStem(stem);
    const basePath = parts.join("/");

    return `${new URL(cdnHost).origin}${basePath}/.hls/${encodeURIComponent(slug)}/playlist.m3u8`;
  } catch {
    return null;
  }
}
