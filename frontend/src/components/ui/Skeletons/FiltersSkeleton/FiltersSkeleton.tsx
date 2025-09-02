import s from "./FiltersSkeleton.module.scss";

interface FiltersSkeletonProps {
  amount?: number;
}

const FiltersSkeleton = ({ amount = 8 }: FiltersSkeletonProps) => {
  return (
    <ul className={s.skeletons}>
      {Array(amount)
        .fill({ length: amount })
        .map((_, index) => (
          <li key={index} className={s.skeleton}></li>
        ))}
    </ul>
  );
};

export default FiltersSkeleton;
