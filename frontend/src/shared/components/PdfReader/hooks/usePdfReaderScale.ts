import {
  DEFAULT_SCALE,
  PDF_READER_SCALE_KEY,
  scales,
  screenResolutionMap,
} from "../constants.ts";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { SingleValue } from "react-select";
import { useSearchParams } from "react-router-dom";

export const usePdfReaderScale = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const screenWidth = useScreenWidth();

  // ✅ Приводим к числу
  const scale = Number(searchParams.get(PDF_READER_SCALE_KEY)) || DEFAULT_SCALE;

  const handleResizePage = () => {
    const sorted = Array.from(screenResolutionMap.values()).sort(
      (a, b) => b.width - a.width,
    );

    for (const bp of sorted) {
      if (screenWidth >= bp.width) {
        return bp.pageWidth;
      }
    }
    return sorted[sorted.length - 1].pageWidth;
  };

  const handleZoom = (direction?: "in" | "out", val?: number) => {
    const newParams = new URLSearchParams(searchParams);
    const currentIndex = scales.findIndex((option) => option.value === scale);
    if (currentIndex === -1) return;

    if (direction === "in" && currentIndex < scales.length - 1) {
      newParams.set(
        PDF_READER_SCALE_KEY,
        String(scales[currentIndex + 1].value),
      );
    } else if (direction === "out" && currentIndex > 0) {
      newParams.set(
        PDF_READER_SCALE_KEY,
        String(scales[currentIndex - 1].value),
      );
    } else if (val) {
      newParams.set(PDF_READER_SCALE_KEY, String(val));
    }

    setSearchParams(newParams, { replace: true });
  };

  const handleScaleSelectChange = (newValue: SingleValue<any>) => {
    if (newValue && typeof newValue.value === "number") {
      handleZoom(undefined, newValue.value);
    }
  };

  return {
    scale,
    handleZoom,
    handleScaleSelectChange,
    handleResizePage,
  };
};
