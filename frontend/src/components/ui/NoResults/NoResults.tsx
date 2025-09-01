import s from "./NoResults.module.scss";
import { NoResultsIcon } from "../../../assets/icons";
import { Trans } from "react-i18next";

const NoResults = () => {
  return (
    <div className={s.no_results}>
      <NoResultsIcon className={s.icon} />
      <p className={s.title}>
        <Trans i18nKey="search.noResults.title" />
      </p>
      <p className={s.desc}>
        <Trans i18nKey="search.noResults.description" />
      </p>
    </div>
  );
};

export default NoResults;
