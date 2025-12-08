import s from "./Select.module.scss";
import { ReactNode, useLayoutEffect, useRef, useState } from "react";
import Option from "./Option.tsx";
import useOutsideClickMulti from "../../../common/hooks/useOutsideClickMulti.ts";

interface SelectProps<T> {
  className?: string;
  options: T[];
  renderTrigger: (open: boolean) => ReactNode;
  onChange: (value: string) => void;
  subtitle?: string;
  radioButtonType?: "checkbox" | "radio";
  activeValue?: string;
}

const Select = <T extends { [key: string]: any }>({
  options,
  className,
  renderTrigger,
  subtitle,
  radioButtonType = "checkbox",
  onChange,
  activeValue,
}: SelectProps<T>) => {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [direction, setDirection] = useState<"up" | "down">("down");
  const [hPlacement, setHPlacement] = useState<"left" | "center" | "right">(
    "center",
  );
  useOutsideClickMulti([menuRef, triggerRef], () => setOpen(false));

  useLayoutEffect(() => {
    if (!open || !triggerRef.current || !menuRef.current) return;

    const triggerRect = triggerRef.current.getBoundingClientRect();
    const menuRect = menuRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;

    // --- Вертикальная логика как у тебя ---
    const viewportHeight = window.innerHeight;
    const spaceBelow = viewportHeight - triggerRect.bottom;
    const spaceAbove = triggerRect.top;
    const estimatedDropdownHeight = 240;

    if (spaceBelow < estimatedDropdownHeight && spaceAbove > spaceBelow) {
      setDirection("up");
    } else {
      setDirection("down");
    }

    // --- Горизонтальная логика (left/center/right) ---

    const triggerCenter = triggerRect.left + triggerRect.width / 2;
    const halfMenu = menuRect.width / 2;

    const fitsCenter =
      triggerCenter - halfMenu >= 0 &&
      triggerCenter + halfMenu <= viewportWidth;

    if (fitsCenter) {
      setHPlacement("center");
      return;
    }

    const fitsRight = triggerRect.left + menuRect.width <= viewportWidth;
    const fitsLeft = triggerRect.right - menuRect.width >= 0;

    if (fitsRight) {
      setHPlacement("right");
    } else if (fitsLeft) {
      setHPlacement("left");
    } else {
      // fallback — выбираем сторону, где больше места
      const spaceRight = viewportWidth - triggerRect.left;
      const spaceLeft = triggerRect.right;

      setHPlacement(spaceRight > spaceLeft ? "right" : "left");
    }
  }, [open]);

  const handleTriggerClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    setOpen((prev) => !prev);
  };

  return (
    <div className={`${s.select_container} ${className ? className : ""}`}>
      <div
        className={s.ref_container}
        ref={triggerRef}
        onClick={handleTriggerClick}
      >
        {renderTrigger(open)}
      </div>

      {open && (
        <div
          ref={menuRef}
          className={`${s.select_menu} ${s.open} ${s[direction]} ${s[hPlacement]}`}
        >
          <h6>{subtitle}</h6>

          <ul className={s.options_wrapper}>
            {options.map((option) => (
              <Option
                key={option.value}
                option={option}
                isActive={activeValue === option.value}
                radioButtonType={radioButtonType}
                onChange={(opt) => {
                  onChange(opt!);
                  setOpen(false);
                }}
              />
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Select;
