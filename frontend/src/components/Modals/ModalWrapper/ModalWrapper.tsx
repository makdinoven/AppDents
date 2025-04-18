import React, { ReactNode, useEffect, useRef, useState } from "react";
import s from "./ModalWrapper.module.scss";
import { Trans } from "react-i18next";
import ModalCloseButton from "../../ui/ModalCloseButton/ModalCloseButton.tsx";

interface ModalWrapperProps {
  title?: string;
  children: ReactNode;
  isOpen: boolean;
  onClose: () => void;
  triggerElement?: HTMLElement | null;
  cutoutPosition: "top-right" | "bottom-right" | "none";
  cutoutOffsetY?: number;
  cutoutOffsetX?: number;
  hasTitle?: boolean;
  hasCloseButton?: boolean;
  isLang?: boolean;
  variant?: "dark" | "default";
}

const ModalWrapper: React.FC<ModalWrapperProps> = ({
  title,
  children,
  isOpen,
  onClose,
  isLang = false,
  hasTitle = true,
  hasCloseButton = true,
  triggerElement,
  cutoutPosition,
  cutoutOffsetY = 20,
  cutoutOffsetX = 30,
  variant = "default",
}) => {
  const [isClosing, setIsClosing] = useState(false);
  const [triggerTop, setTriggerTop] = useState<number | null>(null);
  const [triggerDimensions, setTriggerDimensions] = useState<{
    width: number;
    height: number;
    x: number;
    y: number;
  }>({
    width: 0,
    height: 0,
    x: 0,
    y: 0,
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
          x: triggerRect.x,
          y: triggerRect.y,
        });
        setTriggerTop(triggerRect.top);
      };

      const resizeObserver = new ResizeObserver(updateDimensions);
      resizeObserver.observe(triggerElement);
      window.addEventListener("resize", updateDimensions);

      updateDimensions();

      return () => {
        resizeObserver.disconnect();
        window.removeEventListener("resize", updateDimensions);
      };
    }
  }, [triggerElement, isOpen]);

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
    none: {
      borderRadius: "40px",
    },
  };

  const modalContainerStyles = isLang
    ? {
        maxWidth: "300px",
        width: "fit-content",
        top: triggerTop ? `${triggerTop}px` : "50%",
        right: `calc(100vw - ${triggerDimensions.x + triggerDimensions.width}px)`,
      }
    : cutoutPosition === "none"
      ? {
          top: "50%",
          transform: "translateY(-50%)",
          marginRight: "auto",
          maxWidth: "700px",
          padding: "0 20px",
        }
      : {
          top: triggerTop ? `${triggerTop}px` : "50%",
          padding: "0 20px",
          marginRight: "auto",
        };

  const selectedModalBodyStyle = {
    "top-right": modalContentStyles.topRight,
    "bottom-right": modalContentStyles.bottomRight,
    none: modalContentStyles.none,
  }[cutoutPosition];

  const modalBodyStyle = {
    ...(isLang
      ? { minHeight: "auto", padding: "clamp(14px, 3vw, 20px)" }
      : { minHeight: "495px" }),
    ...(variant === "dark"
      ? { background: "#01433dcc", backdropFilter: "blur(10px)" }
      : {}),
  };

  const finalModalBodyStyle = {
    ...selectedModalBodyStyle,
    ...modalBodyStyle,
  };

  const cutoutStyles = {
    height: `calc(${triggerDimensions.height}px + ${cutoutOffsetY}px)`,
    width: `calc(100% - (${triggerDimensions.width}px + ${cutoutOffsetX}px))`,
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        backgroundColor: `${cutoutPosition === "none" ? "rgba(0, 0, 0, 0.06)" : ""}`,
      }}
      className={`${s.modal_overlay} ${isClosing ? s.fadeOut : s.fadeIn}`}
      onClick={handleClose}
    >
      <div className={s.modal_container} style={modalContainerStyles}>
        {isTopRight && (
          <div
            onClick={(e) => e.stopPropagation()}
            className={`${s.modal_header} ${s.topRight}`}
            style={cutoutStyles}
          >
            {hasCloseButton && (
              <ModalCloseButton
                className={s.close_button}
                onClick={handleClose}
              />
            )}
          </div>
        )}

        <div
          ref={modalContentRef}
          className={s.modal_body}
          onClick={(e) => e.stopPropagation()}
          style={finalModalBodyStyle}
        >
          {!isTopRight && hasCloseButton && (
            <ModalCloseButton
              className={s.close_button}
              onClick={handleClose}
            />
          )}
          {hasTitle && (
            <h3>
              <Trans i18nKey={title} />
            </h3>
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
