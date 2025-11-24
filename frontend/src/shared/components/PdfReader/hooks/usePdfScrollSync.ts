import { useCallback, useEffect, useRef, useState } from "react";

export type UsePdfScrollSyncOpts = {
  containerRef: React.RefObject<HTMLDivElement>;
  totalPages?: number;
  initialPage?: number;
  throttleMs?: number;
  centerOnPage?: boolean;
  settleDelayMs?: number; // таймаут-фолбэк для iOS-инерции (80–150мс)
  visibleThreshold?: number; // доля видимости для фиксации целевой страницы (0.5–0.75)
};

export function usePdfScrollSync({
  containerRef,
  totalPages,
  initialPage = 1,
  throttleMs = 100,
  centerOnPage = true,
  settleDelayMs = 120,
  visibleThreshold = 0.6,
}: UsePdfScrollSyncOpts) {
  const [currentPage, setCurrentPage] = useState<string>(String(initialPage));

  const isProgrammaticScroll = useRef(false);
  const pendingTargetPage = useRef<number | null>(null);
  const scrollOpToken = useRef(0);

  const rafId = useRef<number | null>(null);
  const lastInvoke = useRef<number>(0);
  const settleTimer = useRef<number | null>(null);
  const ioRef = useRef<IntersectionObserver | null>(null);

  const throttled = useCallback(
    (fn: () => void) => {
      const now = performance.now();
      if (now - lastInvoke.current >= throttleMs) {
        lastInvoke.current = now;
        fn();
        return;
      }
      if (rafId.current) cancelAnimationFrame(rafId.current);
      rafId.current = requestAnimationFrame(() => {
        lastInvoke.current = performance.now();
        fn();
      });
    },
    [throttleMs],
  );

  const computeBestVisiblePage = useCallback(() => {
    const container = containerRef.current;
    if (!container || !totalPages) return 1;

    const top = container.scrollTop;
    const bottom = top + container.clientHeight;

    let bestPage = 1;
    let maxVisible = -1;

    for (let i = 1; i <= totalPages; i++) {
      const el = container.querySelector(
        `[data-page="${i}"]`,
      ) as HTMLElement | null;
      if (!el) continue;

      // координаты относительно контейнера
      const elTop =
        el.offsetTop -
        (container.offsetParent === el.offsetParent ? 0 : container.offsetTop);
      const elBottom = elTop + el.offsetHeight;

      const visible = Math.max(
        0,
        Math.min(bottom, elBottom) - Math.max(top, elTop),
      );

      if (visible > maxVisible) {
        maxVisible = visible;
        bestPage = i;
      }
    }
    return bestPage;
  }, [containerRef, totalPages]);

  const handleScroll = useCallback(() => {
    // игнорим во время программного скролла И пока ждём подтверждения целевой страницы
    if (isProgrammaticScroll.current || pendingTargetPage.current != null)
      return;

    throttled(() => {
      const p = computeBestVisiblePage();
      setCurrentPage(String(p));
    });
  }, [computeBestVisiblePage, throttled]);

  // IntersectionObserver: подтверждаем целевую страницу,
  // когда она действительно заняла >= visibleThreshold вьюпорта контейнера
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // очищаем предыдущий IO
    if (ioRef.current) {
      ioRef.current.disconnect();
      ioRef.current = null;
    }

    // создаём новый IO c root = контейнером
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const el = entry.target as HTMLElement;
          const pageAttr = el.getAttribute("data-page");
          if (!pageAttr) continue;
          const pageNum = Number(pageAttr);

          // если это целевая страница и видимость достаточна — фиксируем
          if (
            pendingTargetPage.current === pageNum &&
            entry.intersectionRatio >= visibleThreshold
          ) {
            setCurrentPage(String(pageNum));
            pendingTargetPage.current = null;
            isProgrammaticScroll.current = false;
          }
        }
      },
      {
        root: container,
        threshold: buildThresholds(visibleThreshold),
      },
    );

    // наблюдаем за всеми страницами
    // (если используешь виртуализацию — подключай/отключай наблюдение только на видимые DOM-страницы)
    if (totalPages) {
      for (let i = 1; i <= totalPages; i++) {
        const el = container.querySelector(`[data-page="${i}"]`);
        if (el) io.observe(el);
      }
    }

    ioRef.current = io;
    return () => io.disconnect();
  }, [containerRef, totalPages, visibleThreshold]);

  // scroll listener
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    el.addEventListener("scroll", handleScroll, { passive: true });

    // scrollend — современный способ узнать, что скролл закончен
    const onScrollEnd = () => {
      // если не было программного скролла — просто дофиксируем актуальную страницу
      if (!isProgrammaticScroll.current && pendingTargetPage.current == null) {
        const p = computeBestVisiblePage();
        setCurrentPage(String(p));
      }
    };
    el.addEventListener?.("scrollend", onScrollEnd as EventListener);

    return () => {
      el.removeEventListener("scroll", handleScroll);
      el.removeEventListener?.("scrollend", onScrollEnd as EventListener);
      if (rafId.current) cancelAnimationFrame(rafId.current);
      if (settleTimer.current) window.clearTimeout(settleTimer.current);
    };
  }, [containerRef, handleScroll, computeBestVisiblePage]);

  const scrollToPage = useCallback(
    (target: number) => {
      const container = containerRef.current;
      if (!container || !totalPages) return;

      // отменяем «хвосты»
      if (rafId.current) cancelAnimationFrame(rafId.current);
      if (settleTimer.current) window.clearTimeout(settleTimer.current);

      const myToken = ++scrollOpToken.current;
      const page = Math.max(1, Math.min(totalPages, target));

      pendingTargetPage.current = page;
      isProgrammaticScroll.current = true;

      const el = container.querySelector(
        `[data-page="${page}"]`,
      ) as HTMLElement | null;
      if (!el) {
        // нет DOM-ноды — зафиксируем «оптимистично»
        setCurrentPage(String(page));
        isProgrammaticScroll.current = false;
        pendingTargetPage.current = null;
        return;
      }

      const elTop =
        el.offsetTop -
        (container.offsetParent === el.offsetParent ? 0 : container.offsetTop);

      const targetTop = centerOnPage
        ? elTop - Math.max(0, (container.clientHeight - el.offsetHeight) / 2)
        : elTop;

      container.scrollTo({ top: targetTop, behavior: "auto" });

      // фолбэк: если IO/scrollend не сработают (редко на iOS с инерцией),
      // всё равно снимем блокировку и зафиксируем страницу
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          settleTimer.current = window.setTimeout(() => {
            if (myToken === scrollOpToken.current) {
              setCurrentPage(String(page));
              isProgrammaticScroll.current = false;
              pendingTargetPage.current = null;
            }
          }, settleDelayMs);
        });
      });
    },
    [containerRef, totalPages, centerOnPage, settleDelayMs],
  );

  return { currentPage, setCurrentPage, scrollToPage };
}

function buildThresholds(visibleThreshold: number) {
  // плотная шкала + сам порог (делает IO более стабильным)
  const base = [0, 0.01, 0.1, 0.25, 0.5, visibleThreshold, 0.75, 0.9, 0.99, 1];
  return Array.from(new Set(base)).sort((a, b) => a - b);
}

export function getWindowAround(
  current: number,
  total: number | undefined,
  overscan = 1,
) {
  if (!total) return { start: 1, end: 1 };
  const start = Math.max(1, current - overscan);
  const end = Math.min(total, current + overscan);
  return { start, end };
}
