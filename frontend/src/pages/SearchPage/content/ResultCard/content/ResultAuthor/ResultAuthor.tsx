import s from "./ResultAuthor.module.scss";
import LangLogo from "../../../../../../shared/components/ui/LangLogo/LangLogo.tsx";
import { ResultAuthorData } from "../../../../../../shared/store/slices/mainSlice.ts";
import {
  Arrow,
  BooksIcon,
  CoursesIcon,
} from "../../../../../../shared/assets/icons";
import { Trans } from "react-i18next";
import { useState } from "react";
import { NoUser } from "../../../../../../shared/assets";

const ResultAuthor = ({
  data: { language, name, photo, courses_count, books_count, description },
}: {
  data: ResultAuthorData;
}) => {
  const [imgError, setImgError] = useState<boolean>(false);

  const counts = [
    {
      count: courses_count,
      key: "professor.coursesCount",
      icon: <CoursesIcon className={s.icon} />,
    },
    {
      count: books_count,
      key: "professor.booksCount",
      icon: <BooksIcon className={s.icon} />,
    },
  ];

  const hasCounts = counts.some((item) => item.count > 0);

  return (
    <>
      {/*<ProfessorsIcon className={s.icon} />*/}
      <div className={s.photo_wrapper}>
        <LangLogo className={s.lang_logo} lang={language} />
        {photo && !imgError ? (
          <img
            className={s.photo}
            onError={() => setImgError(true)}
            src={photo}
            alt="author photo"
          />
        ) : (
          <div className={`${s.photo} ${s.no_photo}`}>
            <NoUser />
          </div>
        )}
      </div>
      <div className={s.card_body}>
        <h5 className={s.name}>{name}</h5>

        {hasCounts && (
          <div className={s.count_items}>
            {counts.map(
              (item) =>
                item.count > 0 && (
                  <div key={item.key} className={s.icon_count_container}>
                    {item.icon}
                    <Trans i18nKey={item.key} count={item.count} />
                  </div>
                ),
            )}
          </div>
        )}
        <p className={s.description}>{description}</p>
        <button className={s.button}>
          <Trans i18nKey="professor.about" />
          <Arrow />
        </button>
      </div>
    </>
  );
};

export default ResultAuthor;
