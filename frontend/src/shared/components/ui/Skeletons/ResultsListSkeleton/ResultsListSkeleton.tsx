import s from "./ResultsListSkeleton.module.scss";
import ResultCardSkeleton from "./modules/ResultsCardSkeleton/ResultCardSkeleton.tsx";
import { SearchResultKeysType } from "../../../../store/slices/mainSlice.ts";

const ResultsListSkeleton = ({ types }: { types: SearchResultKeysType[] }) => {
  let type: SearchResultKeysType;

  if (types.length > 1) {
    type = "landings";
  } else {
    type = types[0];
  }

  return (
    <div className={s.list_container}>
      <div className={s.list_title}>
        <span className={s.icon_placeholder} />
        <span className={s.text_placeholder} />
      </div>
      <ul className={s.list}>
        {Array(10)
          .fill({ length: 10 })
          .map((_, index: number) => (
            <ResultCardSkeleton key={index} type={type} />
          ))}
      </ul>
    </div>
  );
};

export default ResultsListSkeleton;
