import { useEffect, useRef, useState } from "react";
import ReactDOM from "react-dom";
import PdfReader from "./PdfReader.tsx";
import s from "./PdfReader.module.scss";
import ModalOverlay from "../../Modals/ModalOverlay/ModalOverlay.tsx";

interface PdfReaderWrapperProps {
  parentId: string;
  url: string;
}

const PdfReaderWrapper = ({ parentId, url }: PdfReaderWrapperProps) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const closeFullscreenRef = useRef<() => void>(null);
  const [isFullScreen, setIsFullScreen] = useState(false);

  useEffect(() => {
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
  }, [parentId, isFullScreen]);

  if (!containerRef.current && isFullScreen) {
    const container = document.createElement("div");
    container.className = s.portal_container;
    containerRef.current = container;
  }

  const handleFullScreen = (state: boolean) => {
    if (!state) {
      closeFullscreenRef.current?.();
    } else {
      setIsFullScreen(state);
    }
  };

  const reader = (
    <PdfReader
      url={url}
      fullScreen={isFullScreen}
      setFullScreen={handleFullScreen}
    />
  );

  return isFullScreen && containerRef.current ? (
    ReactDOM.createPortal(
      <>
        <ModalOverlay
          isVisibleCondition={true}
          modalPosition={"fullscreen"}
          customHandleClose={() => setIsFullScreen(false)}
          onInitClose={(fn) => (closeFullscreenRef.current = fn)}
        >
          {reader}
        </ModalOverlay>
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
