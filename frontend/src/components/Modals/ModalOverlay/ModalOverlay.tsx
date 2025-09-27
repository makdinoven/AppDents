import s from "./ModalOverlay.module.scss";
import { ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { Path } from "../../../routes/routes.ts";
import { useLocation, useNavigate } from "react-router-dom";

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
          navigate(Path.main);
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
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.body.style.overflow = "";
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

  return (
    <div
      onClick={closeModal}
      className={`${s.overlay} ${s[modalPosition]} ${isClosing ? s.closing : s.open}`}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className={`${s.content} ${isClosing ? s.closing : ""}`}
      >
        {children}
      </div>
    </div>
  );
};

export default ModalOverlay;
