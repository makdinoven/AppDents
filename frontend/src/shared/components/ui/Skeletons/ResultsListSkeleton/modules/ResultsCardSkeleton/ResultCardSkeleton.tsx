import s from "./ResultCardSkeleton.module.scss";
import { JSX } from "react";
import { SearchResultKeysType } from "../../../../../../store/slices/mainSlice.ts";
import ResultLandingSkeleton from "./content/ResultLandingSkeleton/ResultLandingSkeleton.tsx";
import ResultAuthorSkeleton from "./content/ResultAuthorSkeleton/ResultAuthorSkeleton.tsx";

const ResultCardSkeleton = ({ type }: { type: SearchResultKeysType }) => {
  let cardContent: JSX.Element;

  switch (type) {
    case "landings":
      cardContent = <ResultLandingSkeleton type={type} />;
      break;

    case "authors":
      cardContent = <ResultAuthorSkeleton />;
      break;

    case "book_landings":
      cardContent = <ResultLandingSkeleton type={type} />;
      break;
  }

  return <li className={s.card_skeleton}>{cardContent}</li>;
};

export default ResultCardSkeleton;
