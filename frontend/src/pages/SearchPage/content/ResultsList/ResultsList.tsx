import s from "./ResultsList.module.scss";
import { Trans } from "react-i18next";
import ResultCard from "../ResultCard/ResultCard.tsx";
import { ResultLandingData } from "../ResultCard/content/ResultLanding/ResultLanding.tsx";
import { ResultAuthorData } from "../ResultCard/content/ResultAuthor/ResultAuthor.tsx";
import { ResultBookData } from "../ResultCard/content/ResultBook/ResultBook.tsx";

const ResultList = ({
  type,
  data,
  quantity,
}: {
  type: "landings" | "authors" | "book_landings";
  quantity: number;
  data: ResultLandingData[] | ResultAuthorData[] | ResultBookData[];
}) => {
  return (
    <>
      <div className={s.list_title}>
        <span>
          <Trans i18nKey={`search.results.${type}`} />:
        </span>
        <span className={s.quantity}>{quantity}</span>
      </div>
      {data.map((item: any, index: number) => (
        <ResultCard key={index} type={type} data={item} />
      ))}
    </>
  );
};

export default ResultList;
