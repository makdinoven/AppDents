import React, { useEffect, useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import s from "./PdfReader.module.scss";
import type { PDFDocumentProxy } from "pdfjs-dist";
import { SingleValue } from "react-select";
import { t } from "i18next";
import ThumbNails from "./ThumbNails/ThumbNails.tsx";
import Loader from "../../ui/Loader/Loader.tsx";
import { useThrottle } from "../../../common/hooks/useThrottle.ts";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { DEFAULT_SCALE, scales, screenResolutionMap } from "./constants.ts";
import PdfHeader from "./PdfHeader/PdfHeader.tsx";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

type SelectType = {
  value: number | string | string[];
  name: string;
};

interface PdfReaderProps {
  url: string | null;
  fullScreen: boolean;
  setFullScreen: (state: boolean) => void;
  currentPage: string;
  setCurrentPage: (val: string) => void;
  fromProfile?: boolean;
}

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

  return (
    <div
      className={`${s.pdf_reader} ${fromProfile ? s.from_profile : ""} ${fullScreen ? s.full_screen : ""} `}
      onClick={handleOverlayClick}
    >
      <PdfHeader
        handleThumbNailsClick={handleThumbNailsClick}
        totalPages={totalPages}
        currentPage={currentPage}
        handleZoom={handleZoom}
        handleInputChange={handleInputChange}
        screenWidth={screenWidth}
        handleSelectChange={handleSelectChange}
        goToNextPage={goToNextPage}
        goToPrevPage={goToPrevPage}
        handleCloseFullScreen={() => setFullScreen(false)}
        handleOpenFullScreen={() => setFullScreen(true)}
        fullScreen={fullScreen}
        scale={scale}
      />
      <div className={`${s.overlay} ${isThumbNailsOpen ? s.open : ""}`}></div>
      <div
        style={{
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
            {fullScreen && (
              <ThumbNails
                isOpen={isThumbNailsOpen}
                totalPages={totalPages}
                handlePageChange={(page) => handleScrollToPage(page)}
                onClick={handleThumbNailsAreaClick}
                currentPage={pageNum}
              />
            )}
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
