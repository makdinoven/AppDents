import s from "./FiltersSkeleton.module.scss";

interface FiltersSkeletonProps {
  amount?: number;
}

const FiltersSkeleton = ({ amount = 3 }: FiltersSkeletonProps) => {
  return (
    <div className={s.container}>
      <ul className={s.skeletons}>
        {Array(amount)
          .fill({ length: amount })
          .map((_, index) => (
            <li key={index} className={s.skeleton}></li>
          ))}
      </ul>
      <div className={s.count}></div>
    </div>
  );
};

export default FiltersSkeleton;
