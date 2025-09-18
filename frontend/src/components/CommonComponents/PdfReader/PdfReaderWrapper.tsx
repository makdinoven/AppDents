import { useRef, useEffect, useState } from "react";
import ReactDOM from "react-dom";
import PdfReader from "./PdfReader.tsx";
import s from "./PdfReader.module.scss";

interface PdfReaderWrapperProps {
  parentId: string;
  url: string;
}

const PdfReaderWrapper = ({ parentId, url }: PdfReaderWrapperProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isFullScreen, setIsFullScreen] = useState(false);

  useEffect(() => {
    const target =
      (parentId && document.getElementById(parentId)) || document.body;

    if (containerRef.current) {
      target.appendChild(containerRef.current);
    }

    if (isFullScreen) {
      document.body.style.overflow = "hidden";
    }

    return () => {
      if (containerRef.current && target.contains(containerRef.current)) {
        target.removeChild(containerRef.current);
        containerRef.current = null;
      }
      document.body.style.overflow = "";
    };
  }, [parentId, isFullScreen]);

  useEffect(() => {
    const viewerState = sessionStorage.getItem("viewerState");
    if (viewerState) {
      setIsFullScreen(JSON.parse(viewerState));
    }
  }, []);

  useEffect(() => {
    sessionStorage.setItem("viewerState", JSON.stringify(isFullScreen));
  }, [isFullScreen]);

  if (!containerRef.current && isFullScreen) {
    const container = document.createElement("div");
    container.className = s.portal_container;
    containerRef.current = container;
  }

  const handleFullScreen = (state: boolean) => {
    setIsFullScreen(state);
  };

  return isFullScreen && containerRef.current ? (
    ReactDOM.createPortal(
      <>
        <PdfReader
          url={url}
          fullScreen={isFullScreen}
          setFullScreen={handleFullScreen}
        />
        <div className={s.wrapper_overlay} />
      </>,
      containerRef.current,
    )
  ) : (
    <PdfReader
      url={url}
      fullScreen={isFullScreen}
      setFullScreen={handleFullScreen}
    />
  );
};
export default PdfReaderWrapper;
