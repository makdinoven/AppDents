import ReactDOM from "react-dom";
import PdfReader from "./PdfReader.tsx";
import ModalOverlay from "../../Modals/ModalOverlay/ModalOverlay.tsx";
import { useEffect, useRef } from "react";
import s from "./PdfReader.module.scss";
import { useSearchParams } from "react-router-dom";
import { PDF_READER_FULLSCREEN_KEY } from "./PdfReaderWrapper.tsx";

interface PdfReaderFullscreenProps {
  url: string;
  parentId?: string;
  currentPage: string;
  setCurrentPage: (val: string) => void;
  usePortal?: boolean;
  fromProfile?: boolean;
}

const PdfReaderFullScreen = ({
  parentId,
  url,
  currentPage,
  setCurrentPage,
  usePortal = true,
  fromProfile,
}: PdfReaderFullscreenProps) => {
  const closeFullScreenRef = useRef<() => void>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const isFullScreen = searchParams.has(PDF_READER_FULLSCREEN_KEY);

  const closeFullScreen = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete(PDF_READER_FULLSCREEN_KEY);
    setSearchParams(newParams, { replace: true });
  };

  useEffect(() => {
    if (!usePortal) return;
    const target =
      (parentId && document.getElementById(parentId)) || document.body;

    if (containerRef.current) {
      target.appendChild(containerRef.current);
    }

    return () => {
      if (containerRef.current && target.contains(containerRef.current)) {
        target.removeChild(containerRef.current);
        containerRef.current = null;
      }
    };
  }, [parentId, isFullScreen, usePortal]);

  if (usePortal && !containerRef.current && isFullScreen) {
    const container = document.createElement("div");
    container.className = s.portal_container;
    containerRef.current = container;
  }

  const content = (
    <ModalOverlay
      isVisibleCondition={true}
      modalPosition={"fullscreen"}
      customHandleClose={closeFullScreen}
      onInitClose={(fn) => (closeFullScreenRef.current = fn)}
    >
      <PdfReader
        fromProfile={fromProfile}
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        url={url}
        fullScreen={true}
        setFullScreen={() => closeFullScreenRef.current?.()}
        key="pdf"
      />
    </ModalOverlay>
  );

  if (!usePortal && isFullScreen) return content;

  return (
    containerRef.current && ReactDOM.createPortal(content, containerRef.current)
  );
};

export default PdfReaderFullScreen;
