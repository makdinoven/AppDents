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
import { Trans } from "react-i18next";
import { t } from "i18next";
import ThumbNails from "./ThumbNails/ThumbNails.tsx";
import { useThrottle } from "../../../common/hooks/useThrottle.ts";
import Loader from "../../ui/Loader/Loader.tsx";

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
  url: string;
  fullScreen: boolean;
  setFullScreen: (state: boolean) => void;
  currentPage: string;
  setCurrentPage: (val: string) => void;
}

const DEFAULT_SCALE = 0.75;

const PdfReader = ({
  url,
  fullScreen,
  setFullScreen,
  currentPage,
  setCurrentPage,
}: PdfReaderProps) => {
  const [totalPages, setTotalPages] = useState<number>();
  const [pageNumber, setPageNumber] = useState<number>(1);
  const documentRef = useRef<HTMLDivElement | null>(null);
  const [screenWidth, setScreenWidth] = useState<number>(window.innerWidth);
  const [scale, setScale] = useState<number>(DEFAULT_SCALE);
  const [isThumbNailsOpen, setIsThumbNailsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isLogicScroll, setIsLogicScroll] = useState(false);
  const throttledHandleScroll = useThrottle(() => {
    if (!documentRef.current || !totalPages) return;
    if (isLogicScroll) {
      setIsLogicScroll(false);
      return;
    }
    const container = documentRef.current;
    const { scrollTop, scrollHeight, clientHeight } = container;

    const maxScrollTop = scrollHeight - clientHeight;

    const progress = scrollTop / maxScrollTop;

    const newPage = Math.min(
      totalPages,
      Math.max(1, Math.round(progress * (totalPages - 1) + 1)),
    );

    setPageNumber(newPage);
  }, 100);

  const options = useMemo(
    () => ({
      cMapUrl: "/cmaps/",
      standardFontDataUrl: "/standard_fonts/",
      wasmUrl: "/wasm/",
    }),
    [],
  );

  useEffect(() => {
    const container = documentRef.current;
    if (!container) return;
    container.addEventListener("scroll", throttledHandleScroll);
    return () => container.removeEventListener("scroll", throttledHandleScroll);
  }, [throttledHandleScroll]);

  useEffect(() => {
    const id = setTimeout(() => {
      setCurrentPage(pageNumber.toString());
    }, 300); // только конечное значение

    return () => clearTimeout(id);
  }, [pageNumber]);

  useEffect(() => {
    const handleResize = () => {
      const newScreenWidth = window.innerWidth;
      setScreenWidth(newScreenWidth);
    };

    handleResize();

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
    };
  }, [screenWidth]);

  const handleResizePage = () => {
    if (screenWidth > screenResolutionMap.get("tablet")!.width) {
      const pageWidth = screenResolutionMap.get("desktop")?.pageWidth;
      if (pageWidth) {
        return pageWidth;
      }
    } else if (
      screenWidth <= screenResolutionMap.get("tablet")!.width &&
      screenWidth > screenResolutionMap.get("mobile")!.width
    ) {
      const pageWidth = screenResolutionMap.get("tablet")?.pageWidth;
      if (pageWidth) {
        return pageWidth;
      }
    } else if (screenWidth <= screenResolutionMap.get("mobile")!.width) {
      const pageWidth = screenResolutionMap.get("mobile")?.pageWidth;
      if (pageWidth) {
        return pageWidth;
      }
    }
  };

  function onDocumentLoadSuccess({
    numPages: nextNumPages,
  }: PDFDocumentProxy): void {
    setTotalPages(nextNumPages);
    setLoading(false);
  }

  const onDocumentLoadError = (error: any) => {
    setError(error.message);
  };
  const handleScrollToPage = (newPage: number) => {
    if (!documentRef.current) return;

    setCurrentPage(newPage.toString());
    setPageNumber(newPage);

    const pageElement = documentRef.current.querySelector(
      `[data-page="${newPage}"]`,
    );
    if (pageElement) {
      const { top } = pageElement.getBoundingClientRect();
      const { top: docTop } = documentRef.current.getBoundingClientRect();
      setIsLogicScroll(true);
      documentRef.current.scrollTop += top - docTop;
    }
  };

  const goToPrevPage = () => {
    const newPage = Math.max(1, pageNumber - 1);
    handleScrollToPage(newPage);
  };

  const goToNextPage = () => {
    const newPage = Math.min(totalPages || 1, pageNumber + 1);
    handleScrollToPage(newPage);
  };

  const handleOpenFullScreen = () => {
    setFullScreen(true);
  };

  const handleCloseFullScreen = () => {
    setFullScreen(false);
  };

  const handleZoomOut = () => {
    setScale((prev) => {
      const currentIndex = scales.findIndex((option) => option.value === prev);
      if (currentIndex > 0 && currentIndex <= scales.length - 1) {
        return scales[currentIndex - 1].value;
      }
      return prev;
    });
  };

  const handleZoomIn = () => {
    setScale((prev) => {
      const currentIndex = scales.findIndex((option) => option.value === prev);
      if (currentIndex >= 0 && currentIndex < scales.length - 1) {
        return scales[currentIndex + 1].value;
      }
      return prev;
    });
  };

  const handleSelectChange = (newValue: SingleValue<SelectType>) => {
    if (newValue) {
      setScale(newValue.value as number);
    }
  };

  const handleGoToPage = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentPage(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const newPage = getPageInputResults(currentPage);
      handleScrollToPage(newPage);
    }
  };

  const getPageInputResults = (inputValue: string): number => {
    setCurrentPage(inputValue.replace(/\D/g, ""));
    const newPage = parseInt(inputValue);
    if (isNaN(newPage) || newPage <= 0) {
      setPageNumber(1);
      return 1;
    } else {
      const validatedPage = Math.max(1, Math.min(totalPages || 1, newPage));
      setPageNumber(validatedPage);
      return validatedPage;
    }
  };

  const handlePageInputBlur = () => {
    getPageInputResults(currentPage);
  };

  const handleThumbNailsClick = () => {
    setIsThumbNailsOpen((prev) => !prev);
  };

  const handlePageChange = (currentPage: number) => {
    setPageNumber(currentPage);
    handleScrollToPage(currentPage);
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
              className={s.page_input}
              value={currentPage === "" ? " " : currentPage}
              onChange={handleGoToPage}
              onKeyDown={handleKeyDown}
              onBlur={handlePageInputBlur}
            />
            {t("of")}
            <span>{totalPages}</span>
          </p>
          <button className={s.expand_button} onClick={handleCloseFullScreen}>
            <MinimizeIcon />
          </button>
        </div>
        <div className={s.right_side}>
          <div className={s.scales_wrapper}>
            <button onClick={handleZoomOut}>
              <ZoomOut />
            </button>
            <button onClick={handleZoomIn}>
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
          {screenWidth > screenResolutionMap.get("mobile")!.width && (
            <div className={s.arrows_wrapper}>
              <button onClick={goToPrevPage} className={s.up}>
                <Chevron />
              </button>
              <button onClick={goToNextPage} className={s.down}>
                <Chevron />
              </button>
            </div>
          )}
        </div>
      </>,
    ],
    [
      false,
      <>
        <div className={s.left_side}>
          <p className={s.page_indicator}>
            <span>
              {pageNumber}/{totalPages}
            </span>
          </p>
          <button className={s.expand_button} onClick={handleOpenFullScreen}>
            <MaximizeIcon />
          </button>
        </div>
        <div className={s.arrows_wrapper}>
          <button onClick={goToPrevPage} className={s.up}>
            <Chevron />
          </button>
          <button onClick={goToNextPage} className={s.down}>
            <Chevron />
          </button>
        </div>
      </>,
    ],
  ]);

  return (
    <div
      className={`${s.pdf_reader} ${fullScreen ? s.full_screen : ""}`}
      onClick={handleOverlayClick}
    >
      <div className={s.header}>{headerContent.get(fullScreen)}</div>
      <ThumbNails
        isOpen={isThumbNailsOpen}
        onLoadSuccess={onDocumentLoadSuccess}
        options={options}
        totalPages={totalPages}
        link={url}
        handlePageChange={handlePageChange}
        onClick={handleThumbNailsAreaClick}
        currentPage={pageNumber}
      />
      <div className={`${s.overlay} ${isThumbNailsOpen && s.open}`}></div>
      <div
        onClick={!fullScreen ? handleOpenFullScreen : undefined}
        style={{ cursor: !fullScreen ? "pointer" : "auto" }}
        className={s.document}
        ref={documentRef}
      >
        {loading ? (
          <div className={s.loading}>
            <Loader />
          </div>
        ) : (
          <Document
            file={url}
            onLoadSuccess={onDocumentLoadSuccess}
            options={options}
            className={s.pages_wrapper}
            loading={false}
            onLoadError={onDocumentLoadError}
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
        {error && (
          <div className={s.error}>
            <Trans i18nKey={"bookLanding.pdfReader.error"} />
          </div>
        )}
      </div>
    </div>
  );
};
export default PdfReader;
