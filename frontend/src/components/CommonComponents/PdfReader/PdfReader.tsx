import { useState, useRef, useEffect, useMemo } from "react";
import { pdfjs, Document, Page } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import s from "./PdfReader.module.scss";
import type { PDFDocumentProxy } from "pdfjs-dist";
import {
  Chevron,
  MaximizeIcon,
  MinimizeIcon,
  ZoomIn,
  ZoomOut,
  ListIcon,
} from "../../../assets/icons";
import { SingleValue } from "react-select";
import MultiSelect from "../MultiSelect/MultiSelect.tsx";
import { Trans, useTranslation } from "react-i18next";
import ThumbNails from "./ThumbNails/ThumbNails.tsx";

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
}

const PdfReader = ({ url, fullScreen, setFullScreen }: PdfReaderProps) => {
  const [totalPages, setTotalPages] = useState<number>();
  const [pageNumber, setPageNumber] = useState<number>(1);
  const pageRef = useRef<HTMLDivElement | null>(null);
  const documentRef = useRef<HTMLDivElement | null>(null);
  const [screenWidth, setScreenWidth] = useState<number>(window.innerWidth);
  const [scale, setScale] = useState<number>(0.5);
  const [inputValue, setInputValue] = useState<string>("1");
  const [isThumbNailsOpen, setIsTumbNailsOpen] = useState(false);

  const { t } = useTranslation();

  const options = useMemo(
    () => ({
      cMapUrl: "/cmaps/",
      standardFontDataUrl: "/standard_fonts/",
      wasmUrl: "/wasm/",
    }),
    [],
  );

  useEffect(() => {
    setInputValue(pageNumber.toString());
  }, [pageNumber]);

  useEffect(() => {
    const userScale = sessionStorage.getItem("pdfScale");
    if (userScale) {
      setScale(JSON.parse(userScale));
    }
  }, []);

  useEffect(() => {
    sessionStorage.setItem("pdfScale", JSON.stringify(scale));
  }, [scale]);

  useEffect(() => {
    if (pageRef.current && documentRef.current) {
      const { top } = pageRef.current.getBoundingClientRect();
      const { top: docTop } = documentRef.current.getBoundingClientRect();
      documentRef.current.scrollTop += top - docTop; // Прокрутка внутри контейнера
    }
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
  }

  const goToPrevPage = () => {
    setPageNumber((prev) => Math.max(1, prev - 1));
  };

  const goToNextPage = () => {
    setPageNumber((prev) => Math.min(totalPages || 1, prev + 1));
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
    setInputValue(e.target.value);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      getPageInputResults(inputValue);
    }
  };

  const getPageInputResults = (inputValue: string) => {
    setInputValue(inputValue.replace(/\D/g, ""));
    const newPage = parseInt(inputValue);
    if (isNaN(newPage) || newPage <= 0) {
      setInputValue("1");
      setPageNumber(1);
    } else if (!isNaN(newPage)) {
      const validatedPage = Math.max(1, Math.min(totalPages || 1, newPage));
      setInputValue(validatedPage.toString());
      setPageNumber(validatedPage);
    }
  };

  const handlePageInputBlur = () => {
    getPageInputResults(inputValue);
  };

  const handleThumbNailsClick = () => {
    setIsTumbNailsOpen((prev) => !prev);
  };

  const handlePageChange = (currentPage: number) => {
    setPageNumber(currentPage);
  };

  const handleOverlayClick = () =>
    isThumbNailsOpen && setIsTumbNailsOpen(false);

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
              value={inputValue === "" ? " " : inputValue}
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
            {!screenResolutionMap.get("mobile") && (
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
          <div className={s.arrows_wrapper}>
            <button onClick={goToPrevPage} className={s.up}>
              <Chevron />
            </button>
            <button onClick={goToNextPage} className={s.down}>
              <Chevron />
            </button>
          </div>
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
      <div className={s.document} ref={documentRef}>
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          options={options}
          className={s.pages_wrapper}
          loading={
            <Trans
              i18nKey={"bookLanding.pdfReader.loading"}
              className={s.loading}
            />
          }
          error={
            <Trans
              i18nKey={"bookLanding.pdfReader.error"}
              className={s.error}
            />
          }
        >
          {Array.from(new Array(totalPages), (_el, index) => (
            <div
              key={index + 1}
              ref={pageNumber === index + 1 ? pageRef : null}
            >
              <Page
                pageNumber={index + 1}
                width={handleResizePage()}
                renderTextLayer={false}
                renderAnnotationLayer={false}
                scale={scale}
              />
            </div>
          ))}
        </Document>
      </div>
    </div>
  );
};
export default PdfReader;
