import React, { useEffect, useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import s from "./PdfReader.module.scss";
import type { PDFDocumentProxy } from "pdfjs-dist";
import {
  Chevron,
  ListIcon,
  MaximizeIcon,
  MinimizeIcon,
  ZoomIn,
  ZoomOut,
} from "../../../assets/icons";
import { SingleValue } from "react-select";
import MultiSelect from "../MultiSelect/MultiSelect.tsx";
import { t } from "i18next";
import ThumbNails from "./ThumbNails/ThumbNails.tsx";
import Loader from "../../ui/Loader/Loader.tsx";
import { useThrottle } from "../../../common/hooks/useThrottle.ts";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

type SelectType = {
  value: number | string | string[];
  name: string;
};

const screenResolutionMap = new Map([
  ["desktop", { width: 1440, pageWidth: 600 }],
  ["middle", { width: 1024, pageWidth: 500 }],
  ["tablet", { width: 768, pageWidth: 450 }],
  ["mobile", { width: 576, pageWidth: 300 }],
]);

export const scales = [
  { value: 0.5, label: "50%" },
  { value: 0.75, label: "75%" },
  { value: 1, label: "100%" },
  { value: 1.25, label: "125%" },
  { value: 1.5, label: "150%" },
  { value: 2, label: "200%" },
];

interface PdfReaderProps {
  url: string | null;
  fullScreen: boolean;
  setFullScreen: (state: boolean) => void;
  currentPage: string;
  setCurrentPage: (val: string) => void;
  fromProfile?: boolean;
}

const DEFAULT_SCALE = 0.75;

const PdfReader = ({
  url,
  fullScreen,
  setFullScreen,
  currentPage,
  setCurrentPage,
  fromProfile = false,
}: PdfReaderProps) => {
  const isProgrammaticScroll = useRef(false);
  const screenWidth = useScreenWidth();
  const [totalPages, setTotalPages] = useState<number>();
  const pageNum = Number(currentPage);
  const documentRef = useRef<HTMLDivElement | null>(null);
  const [isThumbNailsOpen, setIsThumbNailsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);
  const [scale, setScale] = useState<number>(DEFAULT_SCALE);

  const options = useMemo(
    () => ({
      cMapUrl: "/cmaps/",
      standardFontDataUrl: "/standard_fonts/",
      wasmUrl: "/wasm/",
    }),
    [],
  );

  const handleScroll = () => {
    if (!documentRef.current || !totalPages) return;
    const container = documentRef.current;
    const containerTop = container.getBoundingClientRect().top;
    const containerHeight = container.clientHeight;
    let bestPage = 1;
    let maxVisible = 0;
    for (let i = 1; i <= totalPages; i++) {
      const pageElement = container.querySelector(`[data-page="${i}"]`);
      if (!pageElement) continue;
      const rect = pageElement.getBoundingClientRect();
      const visibleTop = Math.max(rect.top, containerTop);
      const visibleBottom = Math.min(
        rect.bottom,
        containerTop + containerHeight,
      );
      const visibleHeight = Math.max(0, visibleBottom - visibleTop);
      if (visibleHeight > maxVisible) {
        maxVisible = visibleHeight;
        bestPage = i;
      }
    }
    setCurrentPage(bestPage.toString());
  };

  const throttledHandleScroll = useThrottle(handleScroll, 100);

  useEffect(() => {
    const container = documentRef.current;
    if (isThumbNailsOpen || !container || isProgrammaticScroll.current) return;
    container.addEventListener("scroll", throttledHandleScroll);
    return () => container.removeEventListener("scroll", throttledHandleScroll);
  }, [isThumbNailsOpen, throttledHandleScroll, isProgrammaticScroll.current]);

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

  const onDocumentLoadSuccess = ({
    numPages: nextNumPages,
  }: PDFDocumentProxy): void => {
    setTotalPages(nextNumPages);
    setLoading(false);
  };

  const onDocumentLoadError = (error: any) => {
    setError(error.message);
    setLoading(false);
  };

  const handleScrollToPage = (newPage: number) => {
    if (!documentRef.current) return;
    setCurrentPage(newPage.toString());

    const pageElement = documentRef.current.querySelector(
      `[data-page="${newPage}"]`,
    );
    if (pageElement) {
      isProgrammaticScroll.current = true;
      const { top } = pageElement.getBoundingClientRect();
      const { top: docTop } = documentRef.current.getBoundingClientRect();
      documentRef.current.scrollTop += top - docTop;
    }

    setTimeout(() => {
      isProgrammaticScroll.current = false;
    }, 0);
  };

  const goToPrevPage = () => {
    const newPage = Math.max(1, pageNum - 1);
    handleScrollToPage(newPage);
  };

  const goToNextPage = () => {
    const newPage = Math.min(totalPages || 1, pageNum + 1);
    handleScrollToPage(newPage);
  };

  const handleOpenFullScreen = () => {
    setFullScreen(true);
  };

  const handleCloseFullScreen = () => {
    setFullScreen(false);
  };

  const handleZoom = (direction: "in" | "out") => {
    setScale((prev) => {
      const currentIndex = scales.findIndex((option) => option.value === prev);
      if (currentIndex === -1) return prev;

      if (direction === "in" && currentIndex < scales.length - 1) {
        return scales[currentIndex + 1].value;
      }

      if (direction === "out" && currentIndex > 0) {
        return scales[currentIndex - 1].value;
      }

      return prev;
    });
  };

  const handleSelectChange = (newValue: SingleValue<SelectType>) => {
    if (newValue) {
      setScale(newValue.value as number);
    }
  };

  const handleInputChange = (newValue: string) => {
    if (newValue === "") {
      setCurrentPage("");
      return;
    }

    let page = Number(newValue);
    if (isNaN(page)) return;

    if (page < 1) page = 1;
    if (totalPages && page > totalPages) page = totalPages;
    setCurrentPage(page.toString());
    handleScrollToPage(page);
  };

  const handleThumbNailsClick = () => {
    setIsThumbNailsOpen((prev) => !prev);
  };

  const handleOverlayClick = () =>
    isThumbNailsOpen && setIsThumbNailsOpen(false);

  const handleThumbNailsAreaClick = (
    event: React.MouseEvent<HTMLDivElement>,
  ) => {
    event.stopPropagation();
  };

  const commonFilterProps = {
    isSearchable: false,
    isMultiple: false,
    valueKey: "value" as const,
    labelKey: "label" as const,
  };

  const findScale = scales.find((option) => option.value === scale);

  const isFirstPage = Number(currentPage) === 1 || !totalPages;
  const isLastPage = Number(currentPage) === Number(totalPages) || !totalPages;

  const renderNextPrevButtons = (
    <div className={s.arrows_wrapper}>
      <button
        onClick={goToPrevPage}
        className={`${s.up} ${isFirstPage ? s.inactive : ""}`}
      >
        <Chevron />
      </button>
      <button
        onClick={goToNextPage}
        className={`${s.down} ${isLastPage ? s.inactive : ""}`}
      >
        <Chevron />
      </button>
    </div>
  );

  const headerContent = new Map([
    [
      true,
      <>
        <div className={s.left_side}>
          <button className={s.list} onClick={handleThumbNailsClick}>
            <ListIcon />
          </button>
          <p className={`${s.page_indicator} ${s.full_screen}`}>
            <input
              type={"number"}
              min={1}
              max={totalPages || 1}
              className={s.page_input}
              value={currentPage === "" ? "" : currentPage}
              onChange={(e) => handleInputChange(e.target.value)}
            />
            {t("of")}
            <span>{totalPages ? totalPages : 0}</span>
          </p>
          <button className={s.expand_button} onClick={handleCloseFullScreen}>
            {fromProfile ? <MaximizeIcon /> : <MinimizeIcon />}
          </button>
        </div>
        <div className={s.right_side}>
          <div className={s.scales_wrapper}>
            <button onClick={() => handleZoom("out")}>
              <ZoomOut />
            </button>
            <button onClick={() => handleZoom("in")}>
              <ZoomIn />
            </button>
            {screenWidth > screenResolutionMap.get("mobile")!.width && (
              <MultiSelect
                {...commonFilterProps}
                id="scales-select"
                placeholder={scale.toString()}
                options={scales}
                selectedValue={findScale?.value as number}
                onChange={handleSelectChange}
                centrate
              />
            )}
          </div>
          {screenWidth > screenResolutionMap.get("mobile")!.width &&
            renderNextPrevButtons}
        </div>
      </>,
    ],
    [
      false,
      <>
        <div className={s.left_side}>
          <p className={s.page_indicator}>
            <span>
              {totalPages ? currentPage : 0}/{totalPages ? totalPages : 0}
            </span>
          </p>
          <button
            className={s.expand_button}
            onClick={handleOpenFullScreen}
            disabled={!totalPages}
          >
            <MaximizeIcon />
          </button>
        </div>
        {screenWidth < screenResolutionMap.get("mobile")!.width && (
          <div className={s.scales_wrapper}>
            <button onClick={() => handleZoom("out")}>
              <ZoomOut />
            </button>
            <button onClick={() => handleZoom("in")}>
              <ZoomIn />
            </button>
          </div>
        )}
        {renderNextPrevButtons}
      </>,
    ],
  ]);

  return (
    <div
      className={`${s.pdf_reader} ${fullScreen ? s.full_screen : ""} ${fromProfile ? s.from_profile : ""}`}
      onClick={handleOverlayClick}
    >
      <div className={s.header}>{headerContent.get(fullScreen)}</div>
      {url && (
        <ThumbNails
          isOpen={isThumbNailsOpen}
          onLoadSuccess={onDocumentLoadSuccess}
          options={options}
          totalPages={totalPages}
          link={url}
          handlePageChange={(page) => handleScrollToPage(page)}
          onClick={handleThumbNailsAreaClick}
          currentPage={pageNum}
        />
      )}
      <div className={`${s.overlay} ${isThumbNailsOpen ? s.open : ""}`}></div>
      <div
        onClick={!fullScreen ? handleOpenFullScreen : undefined}
        style={{
          cursor: !fullScreen ? "pointer" : "auto",
          overflow: isThumbNailsOpen ? "hidden" : "",
        }}
        className={s.document}
        ref={documentRef}
      >
        {url && (
          <Document
            file={url}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            options={options}
            className={s.pages_wrapper}
            loading={false}
            error={false}
          >
            {Array.from(new Array(totalPages), (_el, index) => (
              <div key={index + 1} data-page={index + 1}>
                <Page
                  pageNumber={index + 1}
                  width={handleResizePage()}
                  renderTextLayer={false}
                  renderAnnotationLayer={false}
                  scale={scale}
                  loading={false}
                />
              </div>
            ))}
          </Document>
        )}
        {url && loading && <Loader className={s.loading} />}
        {!url ||
          (error && (
            <p className={s.error}>{t("bookLanding.pdfReader.error")}</p>
          ))}
      </div>
    </div>
  );
};
export default PdfReader;
