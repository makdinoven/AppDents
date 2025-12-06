import { useCallback, useLayoutEffect, useRef, useState } from "react";
import { SelectedUI } from "../../model/types.ts";

const GAP_PX = 10;
const SCROLL_STEP = 300;

type LayoutResult = {
  row1: SelectedUI[];
  row2: SelectedUI[];
  containerRef: React.RefObject<HTMLDivElement>;
  measureRef: React.RefObject<HTMLDivElement>;
  canScrollLeft: boolean;
  canScrollRight: boolean;
  scrollLeft: () => void;
  scrollRight: () => void;
};

export const useSelectedFiltersLayout = (items: SelectedUI[]): LayoutResult => {
  const [rows, setRows] = useState<SelectedUI[][]>([items]);
  const containerRef = useRef<HTMLDivElement>(null!);
  const measureRef = useRef<HTMLDivElement>(null!);

  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // -----------------------------
  // Раскладка по строкам (1 или 2)
  // -----------------------------
  useLayoutEffect(() => {
    const measure = measureRef.current;
    const container = containerRef.current;

    if (!measure || !container || items.length === 0) {
      setRows([items]);
      return;
    }

    const chipNodes = Array.from(measure.children) as HTMLElement[];
    if (chipNodes.length === 0) {
      setRows([items]);
      return;
    }

    const widths = chipNodes.map((node) => node.getBoundingClientRect().width);

    const totalWidth =
      widths.reduce((sum, w) => sum + w, 0) +
      GAP_PX * Math.max(0, widths.length - 1);

    const containerWidth = container.clientWidth;

    // Всё помещается в одну строку → не усложняем
    if (containerWidth && totalWidth <= containerWidth) {
      setRows([items]);
      return;
    }

    // Балансируем элементы между двумя строками по суммарной ширине
    const row1: SelectedUI[] = [];
    const row2: SelectedUI[] = [];
    let width1 = 0;
    let width2 = 0;

    items.forEach((item, index) => {
      const w = widths[index] ?? 0;

      const extra1 = row1.length > 0 ? GAP_PX : 0;
      const extra2 = row2.length > 0 ? GAP_PX : 0;

      if (width1 + extra1 <= width2 + extra2) {
        row1.push(item);
        width1 += w + extra1;
      } else {
        row2.push(item);
        width2 += w + extra2;
      }
    });

    setRows(row2.length === 0 ? [row1] : [row1, row2]);
  }, [items]);

  // -----------------------------
  // Обновление состояния стрелок
  // -----------------------------
  const updateScrollState = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    const { scrollLeft, scrollWidth, clientWidth } = el;
    const maxScrollLeft = scrollWidth - clientWidth;

    // Если нет горизонтального overflow — стрелок быть не должно
    if (scrollWidth <= clientWidth + 1) {
      setCanScrollLeft(false);
      setCanScrollRight(false);
      return;
    }

    setCanScrollLeft(scrollLeft > 2);
    setCanScrollRight(scrollLeft < maxScrollLeft - 2);
  }, []);

  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    // IMPORTANT: вызываем после того, как rows уже посчитаны
    updateScrollState();

    const handleScroll = () => updateScrollState();
    const handleResize = () => updateScrollState();

    el.addEventListener("scroll", handleScroll);
    window.addEventListener("resize", handleResize);

    return () => {
      el.removeEventListener("scroll", handleScroll);
      window.removeEventListener("resize", handleResize);
    };
  }, [updateScrollState, rows]); // ← ключевое: зависимость от rows

  // -----------------------------
  // Скролл по кнопкам
  // -----------------------------
  const scrollByDirection = useCallback((direction: "left" | "right") => {
    const el = containerRef.current;
    if (!el) return;

    const delta = direction === "left" ? -SCROLL_STEP : SCROLL_STEP;

    el.scrollBy({
      left: delta,
      behavior: "smooth",
    });
  }, []);

  const [row1, row2] = rows.length === 1 ? [rows[0], []] : [rows[0], rows[1]];

  return {
    row1,
    row2,
    containerRef,
    measureRef,
    canScrollLeft,
    canScrollRight,
    scrollLeft: () => scrollByDirection("left"),
    scrollRight: () => scrollByDirection("right"),
  };
};
