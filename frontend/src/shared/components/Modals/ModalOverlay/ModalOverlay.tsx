import s from "./ModalOverlay.module.scss";
import { ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { RemoveScroll } from "react-remove-scroll";
import { PATHS } from "../../../../app/routes/routes.ts";

const ModalOverlay = ({
  children,
  isVisibleCondition,
  isUsedAsPage = false,
  modalPosition,
  onInitClose,
  customHandleClose,
}: {
  children: ReactNode;
  isVisibleCondition: boolean;
  isUsedAsPage?: boolean;
  modalPosition: "right" | "top" | "fullscreen";
  onInitClose?: (fn: () => void) => void;
  customHandleClose?: () => void;
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isClosing, setIsClosing] = useState(false);
  const [isVisible, setIsVisible] = useState(isVisibleCondition);
  const closeTimeoutRef = useRef<number | null>(null);

  const closeModal = () => {
    setIsClosing(true);
    if (closeTimeoutRef.current) clearTimeout(closeTimeoutRef.current);
    closeTimeoutRef.current = window.setTimeout(() => {
      setIsClosing(false);
      setIsVisible(false);

      if (isUsedAsPage) {
        if (location.state?.backgroundLocation) {
          navigate(-1);
        } else {
          navigate(PATHS.MAIN);
        }
      }

      customHandleClose?.();
    }, 300);
  };

  useEffect(() => {
    onInitClose?.(closeModal);
  }, [onInitClose]);

  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === "Escape") closeModal();
  }, []);

  useEffect(() => {
    if (!isVisible) return;
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isVisible]);

  useEffect(() => {
    if (isVisibleCondition) {
      setIsVisible(true);
    } else if (isVisible && !isVisibleCondition) {
      closeModal();
    }
  }, [isVisibleCondition]);

  useEffect(() => {
    return () => {
      if (closeTimeoutRef.current) clearTimeout(closeTimeoutRef.current);
    };
  }, []);

  if (!isVisible) return null;

  const shouldRenderChildren = isVisibleCondition || isClosing;

  return (
    <RemoveScroll forwardProps>
      <div
        onClick={closeModal}
        className={`${s.overlay} ${s[modalPosition]} ${isClosing ? s.closing : s.open} 'scroll'`}
      >
        <div
          onClick={(e) => e.stopPropagation()}
          className={`${s.content} ${isClosing ? s.closing : ""}`}
        >
          {shouldRenderChildren && children}
        </div>
      </div>
    </RemoveScroll>
  );
};

export default ModalOverlay;
