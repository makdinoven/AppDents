import s from "./FilterChip.module.scss";

interface FilterChipProps {
  text: React.ReactNode;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const FilterChip = ({
  text,
  iconLeft,
  iconRight,
  className,
  onClick,
}: FilterChipProps) => {
  return (
    <div
      className={`${s.filter_chip} ${className ? className : ""}`}
      onClick={onClick}
    >
      {iconLeft && iconLeft}
      {text}
      {iconRight && iconRight}
    </div>
  );
};
export default FilterChip;
