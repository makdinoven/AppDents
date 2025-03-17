import React, { ReactNode, useEffect, useState, useRef } from "react";
import s from "./ModalWrapper.module.scss";
import ModalClose from "../../../common/Icons/ModalClose.tsx";

interface ModalWrapperProps {
  children: ReactNode;
  isOpen: boolean;
  onClose: () => void;
  triggerElement: HTMLElement | null;
  cutoutPosition: "top-right" | "bottom-right";
  cutoutOffsetY?: number;
  cutoutOffsetX?: number;
}

const ModalWrapper: React.FC<ModalWrapperProps> = ({
  children,
  isOpen,
  onClose,
  triggerElement,
  cutoutPosition,
  cutoutOffsetY = 20,
  cutoutOffsetX = 40,
}) => {
  const [isClosing, setIsClosing] = useState(false);
  const [triggerTop, setTriggerTop] = useState<number | null>(null);
  const [triggerBottom, setTriggerBottom] = useState<number | null>(null);
  const [triggerDimensions, setTriggerDimensions] = useState<{
    width: number;
    height: number;
  }>({
    width: 0,
    height: 0,
  });
  const isTopRight = cutoutPosition === "top-right";
  const isBottomRight = cutoutPosition === "bottom-right";

  const modalContentRef = useRef<HTMLDivElement | null>(null);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      onClose();
      // if (triggerElement) {
      //   triggerElement.style.removeProperty("z-index");
      // }
    }, 150);
  };

  useEffect(() => {
    if (triggerElement) {
      const updateDimensions = () => {
        const triggerRect = triggerElement.getBoundingClientRect();
        // triggerElement.style.zIndex = "2000";
        setTriggerDimensions({
          width: triggerRect.width,
          height: triggerRect.height,
        });
        setTriggerTop(triggerRect.top);
        setTriggerBottom(triggerRect.top - triggerRect.bottom);
        console.log(triggerRect);
      };

      const resizeObserver = new ResizeObserver(updateDimensions);
      resizeObserver.observe(triggerElement);

      updateDimensions();

      return () => {
        resizeObserver.disconnect();
      };
    }
  }, [triggerElement]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === "Escape") {
          onClose();
        }
      };
      document.addEventListener("keydown", handleKeyDown);

      return () => {
        document.body.style.overflow = "";
        document.removeEventListener("keydown", handleKeyDown);
      };
    } else {
      document.body.style.overflow = "";
    }
  }, [isOpen, onClose]);

  const modalContentStyles = {
    topRight: {
      borderTopRightRadius: "20px",
      borderTopLeftRadius: "0",
    },
    bottomRight: {
      borderBottomRightRadius: "20px",
      borderBottomLeftRadius: "0",
    },
  };

  const selectedModalContentStyle = {
    "top-right": modalContentStyles.topRight,
    "bottom-right": modalContentStyles.bottomRight,
  }[cutoutPosition];

  const cutoutStyles = {
    height: `calc(${triggerDimensions.height}px + ${cutoutOffsetY}px)`,
    width: `calc(100% - (${triggerDimensions.width}px + ${cutoutOffsetX}px))`,
  };

  if (!isOpen) return null;

  return (
    <div
      className={`${s.modal_overlay} ${isClosing ? s.fadeOut : s.fadeIn}`}
      onClick={handleClose}
    >
      <div
        className={s.modal_container}
        style={
          isTopRight
            ? { top: triggerTop ? `${triggerTop}px` : "50%" }
            : { bottom: `${triggerBottom}px` }
        }
      >
        {isTopRight && (
          <div
            onClick={(e) => e.stopPropagation()}
            className={`${s.modal_header} ${s.topRight}`}
            style={cutoutStyles}
          >
            <button className={s.close_button} onClick={handleClose}>
              <ModalClose />
            </button>
          </div>
        )}

        <div
          ref={modalContentRef}
          className={s.modal_body}
          onClick={(e) => e.stopPropagation()}
          style={selectedModalContentStyle}
        >
          {isBottomRight && (
            <button className={s.close_button} onClick={handleClose}>
              <ModalClose />
            </button>
          )}
          {children}
        </div>

        {isBottomRight && (
          <div
            onClick={(e) => e.stopPropagation()}
            className={`${s.modal_bottom} ${isBottomRight ? s.bottomRight : ""}`}
            style={cutoutStyles}
          ></div>
        )}
      </div>
    </div>
  );
};

export default ModalWrapper;
