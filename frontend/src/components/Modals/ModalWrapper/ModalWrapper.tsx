import React, {
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Trans } from "react-i18next";
import ModalCloseButton from "../../ui/ModalCloseButton/ModalCloseButton.tsx";
import s from "./ModalWrapper.module.scss";

type CutoutPosition = "top-right" | "top-left" | "bottom-right" | "none";
type ModalVariant = "dark" | "default";

interface ModalWrapperProps {
  title?: string;
  children: ReactNode;
  isOpen: boolean;
  onClose: () => void;
  triggerElement?: HTMLElement | null;
  cutoutPosition: CutoutPosition;
  cutoutOffsetY?: number;
  cutoutOffsetX?: number;
  hasTitle?: boolean;
  hasCloseButton?: boolean;
  isDropdown?: boolean;
  variant?: ModalVariant;
}

type TriggerDimensions = {
  width: number;
  height: number;
  x: number;
  y: number;
  top: number;
};

const ANIMATION_DURATION = 150;
const DEFAULT_BORDER_RADIUS = "40px";

const ModalWrapper: React.FC<ModalWrapperProps> = ({
  title,
  children,
  isOpen,
  onClose,
  isDropdown = false,
  hasTitle = true,
  hasCloseButton = true,
  triggerElement,
  cutoutPosition,
  cutoutOffsetY = 20,
  cutoutOffsetX = 30,
  variant = "default",
}) => {
  const [isClosing, setIsClosing] = useState(false);
  const [triggerDimensions, setTriggerDimensions] = useState<TriggerDimensions>(
    {
      width: 0,
      height: 0,
      x: 0,
      y: 0,
      top: 0,
    },
  );

  const modalContentRef = useRef<HTMLDivElement | null>(null);
  const showTopCutout =
    cutoutPosition === "top-right" || cutoutPosition === "top-left";
  const showBottomCutout = cutoutPosition === "bottom-right";

  const handleClose = useCallback(() => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      onClose();
    }, ANIMATION_DURATION);
  }, [onClose]);

  const variantStyles = useMemo(
    (): React.CSSProperties => ({
      ...(variant === "dark" && {
        background: "#01433dcc",
        backdropFilter: "blur(10px)",
      }),
    }),
    [variant],
  );

  const cutoutStyles = useMemo(
    (): React.CSSProperties => ({
      height: `calc(${triggerDimensions.height}px + ${cutoutOffsetY}px)`,
      width: `calc(100% - (${triggerDimensions.width}px + ${cutoutOffsetX}px))`,
    }),
    [triggerDimensions, cutoutOffsetY, cutoutOffsetX],
  );

  const modalContainerStyles = useMemo((): React.CSSProperties => {
    if (triggerElement) {
      if (isDropdown) {
        if (cutoutPosition === "top-right") {
          return {
            maxWidth: "300px",
            width: "fit-content",
            top: `${triggerDimensions.top}px`,
            right: `calc(100vw - ${triggerDimensions.x + triggerDimensions.width}px)`,
          };
        } else if (cutoutPosition === "top-left") {
          return {
            maxWidth: "205px",
            width: "fit-content",
            top: `${triggerDimensions.top}px`,
            left: `calc(${triggerDimensions.x}px)`,
            marginLeft: "unset",
            marginRight: "auto",
          };
        }
      }

      return cutoutPosition === "none"
        ? {
            top: "50%",
            transform: "translateY(-50%)",
            marginRight: "auto",
            maxWidth: "800px",
            padding: "0 10px",
          }
        : {
            top: `${triggerDimensions.top}px`,
            padding: "0 20px",
            marginRight: "auto",
          };
    }

    return {
      top: "50%",
      transform: "translateY(-50%)",
      marginRight: "auto",
      maxWidth: "800px",
      padding: "0 10px",
    };
  }, [isDropdown, cutoutPosition, triggerDimensions, triggerElement]);

  const modalContentStyles = useMemo((): React.CSSProperties => {
    const baseStyles = {
      "top-right": {
        borderTopRightRadius: "20px",
        borderTopLeftRadius: "0",
      },
      "top-left": {
        borderTopLeftRadius: "20px",
        borderTopRightRadius: "0",
      },
      "bottom-right": {
        borderBottomRightRadius: "20px",
        borderBottomLeftRadius: "0",
      },
      none: {
        borderRadius: DEFAULT_BORDER_RADIUS,
        minHeight: "unset",
      },
    }[cutoutPosition];

    const sizeStyles = isDropdown
      ? {
          minHeight: "auto",
          padding: "clamp(14px, 3vw, 20px)",
        }
      : {};

    return { ...baseStyles, ...sizeStyles, ...variantStyles };
  }, [cutoutPosition, isDropdown, variantStyles]);

  useEffect(() => {
    if (!triggerElement || !isOpen) return;

    const updateDimensions = () => {
      const rect = triggerElement.getBoundingClientRect();
      setTriggerDimensions({
        width: rect.width,
        height: rect.height,
        x: rect.x,
        y: rect.y,
        top: rect.top,
      });
    };

    const resizeObserver = new ResizeObserver(updateDimensions);
    resizeObserver.observe(triggerElement);
    window.addEventListener("resize", updateDimensions);
    updateDimensions();

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", updateDimensions);
    };
  }, [triggerElement, isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className={`${s.modal_overlay} ${isClosing ? s.fadeOut : s.fadeIn}`}
      style={{
        backgroundColor: isDropdown ? "" : "rgba(0, 0, 0, 0.06)",
      }}
      onClick={handleClose}
    >
      <div className={s.modal_container} style={modalContainerStyles}>
        {showTopCutout && (
          <div
            className={`${s.modal_header} ${cutoutPosition === "top-right" ? s.topRight : s.topLeft}`}
            style={cutoutStyles}
            onClick={(e) => e.stopPropagation()}
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
          style={modalContentStyles}
          onClick={(e) => e.stopPropagation()}
        >
          {!showTopCutout && hasCloseButton && (
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

        {showBottomCutout && (
          <div
            className={`${s.modal_bottom} ${s.bottomRight}`}
            style={cutoutStyles}
            onClick={(e) => e.stopPropagation()}
          />
        )}
      </div>
    </div>
  );
};

export default ModalWrapper;
