import s from "./FilterChip.module.scss";
import { ReactNode } from "react";
import { Chevron } from "../../../assets/icons";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";

interface FilterChipProps {
  text: ReactNode;
  iconLeft?: ReactNode;
  iconRight?: ReactNode;
  className?: string;
  onClick?: () => void;
  isActive?: boolean;
  variant?: "dropdown" | "selectedFilter";
  loading?: boolean;
  badgeCount?: number;
  showBadge?: boolean;
}

const FilterChip = ({
  text,
  badgeCount,
  showBadge,
  iconLeft,
  iconRight,
  className,
  onClick,
  isActive,
  variant,
  loading,
}: FilterChipProps) => {
  return (
    <div
      className={`${s.filter_chip} ${variant ? s[variant] : ""} ${className ? className : ""} ${isActive ? s.active : ""}`}
      onClick={onClick}
    >
      {loading && <LoaderOverlay />}
      {iconLeft && iconLeft}
      {showBadge && !!badgeCount && badgeCount > 0 && (
        <span className={s.badge}>{badgeCount}</span>
      )}
      {text}
      {!iconRight && variant === "dropdown" && (
        <Chevron
          className={`${s.dropdown_chevron} ${isActive ? s.open : ""}`}
        />
      )}
      {iconRight && iconRight}
    </div>
  );
};

export default FilterChip;
