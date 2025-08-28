import SearchCourseCard from "../SearchCards/SearchCourseCard/SearchCourseCard.tsx";
import s from "./ResultsList.module.scss";
import { Trans } from "react-i18next";
import SearchAuthorCard from "../SearchCards/SearchAuthorCard/SearchAuthorCard.tsx";

const cardMap = {
  landings: SearchCourseCard,
  authors: SearchAuthorCard,
  // book_landings: SearchBookCard,
};

const ResultList = ({
  type,
  data,
  quantity,
}: {
  type: "landings" | "authors"; // |"book_landings" ;
  quantity: number;
  data: any;
}) => {
  const CardComponent = cardMap[type];

  return (
    <>
      <div className={s.list_title}>
        <span>
          <Trans i18nKey={`search.results.${type}`} />
        </span>
        <span className={s.quantity}>{quantity}</span>
      </div>
      {data.map((item: any, index: number) => (
        <CardComponent key={index} data={item} />
      ))}
    </>
  );
};

export default ResultList;
