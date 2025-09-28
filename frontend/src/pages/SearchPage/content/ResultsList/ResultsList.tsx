import s from "./ResultsList.module.scss";
import { Trans } from "react-i18next";
import ResultCard from "../ResultCard/ResultCard.tsx";
import {
  ResultAuthorData,
  ResultBookData,
  ResultLandingData,
  SearchResultKeysType,
} from "../../../../store/slices/mainSlice.ts";
import {
  BooksIcon,
  CoursesIcon,
  ProfessorsIcon,
} from "../../../../assets/icons";

const ResultsList = ({
  type,
  data,
  quantity,
  customTitle,
}: {
  type: SearchResultKeysType;
  quantity: number;
  data: ResultLandingData[] | ResultAuthorData[] | ResultBookData[];
  customTitle?: string;
}) => {
  const resultIcons: Record<SearchResultKeysType, any> = {
    landings: <CoursesIcon />,
    authors: <ProfessorsIcon />,
    book_landings: <BooksIcon />,
  };

  return (
    <>
      <div className={s.list_title}>
        <span className={s.icon}>{resultIcons[type]}</span>
        {!customTitle ? (
          <span>
            <Trans i18nKey={`search.${type}Result.result`} count={quantity} />
          </span>
        ) : (
          <span className={s.custom_title}>{customTitle}</span>
        )}
      </div>
      {data.map((item: any, index: number) => (
        <ResultCard key={index} type={type} data={item} />
      ))}
    </>
  );
};

export default ResultsList;
