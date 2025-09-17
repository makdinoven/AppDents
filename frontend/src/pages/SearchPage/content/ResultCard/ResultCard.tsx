import s from "./ResultCard.module.scss";
import { Path } from "../../../../routes/routes.ts";
import { useNavigate } from "react-router-dom";
import { JSX } from "react";
import {
  ResultAuthorData,
  ResultBookData,
  ResultLandingData,
} from "../../../../store/slices/mainSlice.ts";
import ResultLanding from "./content/ResultLanding/ResultLanding.tsx";
import ResultAuthor from "./content/ResultAuthor/ResultAuthor.tsx";

type ResultCardProps =
  | { type: "landings"; data: ResultLandingData }
  | { type: "authors"; data: ResultAuthorData }
  | { type: "book_landings"; data: ResultBookData };

const ResultCard = ({ type, data }: ResultCardProps) => {
  const navigate = useNavigate();

  const navigateToResult = () => {
    if (type === "landings") {
      navigate(`/${Path.landingClient}/${data.page_name}`);
    } else if (type === "authors") {
      navigate(`${Path.professor}/${data.id}`);
    } else if (type === "book_landings") {
      // navigate(`/${Path.book}/${data.id}`);
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  let cardContent: JSX.Element;

  switch (type) {
    case "landings":
      cardContent = (
        <ResultLanding type={"landing"} data={data as ResultLandingData} />
      );

      break;

    case "authors":
      cardContent = <ResultAuthor data={data as ResultAuthorData} />;
      break;

    case "book_landings":
      cardContent = <ResultLanding type={"book_landing"} data={data as any} />;
      break;
  }

  return (
    <li onClick={navigateToResult} className={s.card}>
      {cardContent}
    </li>
  );
};

export default ResultCard;
