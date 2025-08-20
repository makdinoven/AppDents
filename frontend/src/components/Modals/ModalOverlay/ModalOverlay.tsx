import s from "./ModalOverlay.module.scss";
import { ReactNode, useEffect, useState } from "react";
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
  modalPosition: "right" | "top";
  onInitClose?: (fn: () => void) => void;
  customHandleClose?: () => void;
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isClosing, setIsClosing] = useState(false);
  const [isVisible, setIsVisible] = useState(isVisibleCondition);

  useEffect(() => {
    if (onInitClose) {
      onInitClose(closeModal);
    }
  }, []);

  const closeModal = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      setIsVisible(false);

      if (isUsedAsPage) {
        if (location.state?.backgroundLocation) {
          navigate(-1);
        } else {
          navigate(Path.main);
        }
      }

      if (customHandleClose) {
        customHandleClose?.();
      }
    }, 300);
  };

  useEffect(() => {
    if (!isVisible) return;

    // const handleEscape = (e: KeyboardEvent) =>
    //   e.key === "Escape" && closeModal();
    document.body.style.overflow = "hidden";
    // document.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = "";
      // document.removeEventListener("keydown", handleEscape);
    };
  }, [isVisible]);

  useEffect(() => {
    if (isVisibleCondition) {
      setIsVisible(true);
    } else {
      closeModal();
    }
  }, [isVisibleCondition]);

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
