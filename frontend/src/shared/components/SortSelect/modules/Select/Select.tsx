import s from "./Select.module.scss";
import { useEffect, useRef, useState } from "react";
import Option from "./Option.tsx";
import useOutsideClick from "../../../../common/hooks/useOutsideClick.ts";

interface SelectProps<T> {
  options: T[];
  trigger: React.ReactNode;
  onChange: (value: string) => void;
  isOpen: boolean;
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>;
  subtitle?: string;
  radioButtonType?: "checkbox" | "radio";
  activeValue?: string;
}

const Select = <T extends { [key: string]: any }>({
  options,
  trigger,
  subtitle,
  radioButtonType = "checkbox",
  onChange,
  isOpen,
  setIsOpen,
  activeValue,
}: SelectProps<T>) => {
  const selectRef = useRef<HTMLDivElement>(null);
  const [direction, setDirection] = useState<"up" | "down">("down");

  const defineDirection = () => {
    if (selectRef.current) {
      const rect = selectRef.current.getBoundingClientRect();

      if (!rect) return;

      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      const dropdownHeight = 374;

      if (spaceBelow < dropdownHeight && spaceAbove > spaceBelow) {
        setDirection("up");
      } else {
        setDirection("down");
      }
    }
  };

  useEffect(() => {
    if (!isOpen) return;

    defineDirection();

    const handleScroll = () => defineDirection();
    const handleResize = () => defineDirection();

    window.addEventListener("scroll", handleScroll, true);
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("scroll", handleScroll, true);
      window.removeEventListener("resize", handleResize);
    };
  }, [isOpen]);

  const handleSelectClick = () => {
    setIsOpen((prev) => !prev);
  };

  useOutsideClick(selectRef, () => setIsOpen(false));

  //...

  return (
    <div className={s.select_container}>
      <div onClick={() => handleSelectClick()}>{trigger}</div>
      <div
        className={`${s.select_menu} ${isOpen ? s.open : ""} ${s[direction]}`}
        ref={selectRef}
      >
        <h6>{subtitle}</h6>
        <ul className={s.options_wrapper}>
          {options.length > 0 &&
            options.map((option) => (
              <Option
                key={option.value}
                option={option}
                radioButtonType={radioButtonType}
                onChange={onChange}
                activeValue={activeValue}
              />
            ))}
        </ul>
      </div>
    </div>
  );
};

export default Select;
