import { useMemo, useRef, useState } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import s from "./PdfReader.module.scss";
import type { PDFDocumentProxy } from "pdfjs-dist";
import { t } from "i18next";
import ThumbNails from "./ThumbNails/ThumbNails.tsx";
import Loader from "../ui/Loader/Loader.tsx";
import PdfHeader from "./PdfHeader/PdfHeader.tsx";
import { RemoveScroll } from "react-remove-scroll";
import { usePdfScrollSync } from "./hooks/usePdfScrollSync.ts";
import { usePdfReaderFullscreen } from "./hooks/usePdfReaderFullscreen.ts";
import { usePdfReaderScale } from "./hooks/usePdfReaderScale.ts";

interface PdfReaderProps {
  url: string | null;
  fromProfile?: boolean;
}

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

const PdfReader = ({ url, fromProfile = false }: PdfReaderProps) => {
  const [totalPages, setTotalPages] = useState<number>();
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [isThumbNailsOpen, setIsThumbNailsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<any>(null);

  const { scale, handleResizePage } = usePdfReaderScale();
  const { fullScreen } = usePdfReaderFullscreen();

  const { currentPage, scrollToPage } = usePdfScrollSync({
    containerRef: scrollRef as any,
    totalPages,
    initialPage: 1,
    throttleMs: 100,
    centerOnPage: true,
  });

  const handleScrollToPage = (p: number) => scrollToPage(p);
  const handleOverlayClick = () =>
    isThumbNailsOpen && setIsThumbNailsOpen(false);

  const onDocumentLoadSuccess = ({ numPages }: PDFDocumentProxy): void => {
    setTotalPages(numPages);
    setLoading(false);
  };
  const onDocumentLoadError = (error: any) => {
    setError(error.message);
    setLoading(false);
  };

  const options = useMemo(
    () => ({
      cMapUrl: "/cmaps/",
      standardFontDataUrl: "/standard_fonts/",
      wasmUrl: "/wasm/",
      disableStream: false,
      disableAutoFetch: true,
      rangeChunkSize: 65536 * 8,
    }),
    [],
  );

  return (
    <RemoveScroll enabled={fullScreen}>
      <div
        className={`${s.pdf_reader} ${fromProfile ? s.from_profile : ""} ${fullScreen ? s.full_screen : ""}`}
        onClick={handleOverlayClick}
      >
        <PdfHeader
          handleScrollToPage={handleScrollToPage}
          handleThumbNailsClick={() => setIsThumbNailsOpen((prev) => !prev)}
          totalPages={totalPages}
          currentPage={currentPage}
        />
        <div className={`${s.overlay} ${isThumbNailsOpen ? s.open : ""}`} />
        <div
          ref={scrollRef}
          className={s.document}
          style={{ overflow: isThumbNailsOpen ? "hidden" : "" }}
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
                  handlePageChange={handleScrollToPage}
                  currentPage={Number(currentPage)}
                />
              )}

              {Array.from({ length: totalPages ?? 0 }, (_, i) => i + 1).map(
                (n) => (
                  <div key={n} data-page={n}>
                    <Page
                      pageNumber={n}
                      width={handleResizePage()}
                      renderTextLayer={false}
                      renderAnnotationLayer={false}
                      scale={Number(scale)}
                      loading={false}
                    />
                  </div>
                ),
              )}
            </Document>
          )}

          {url && loading && <Loader className={s.loading} />}
          {(!url || error) && (
            <p className={s.error}>{t("bookLanding.pdfReader.error")}</p>
          )}
        </div>
      </div>
    </RemoveScroll>
  );
};

export default PdfReader;
