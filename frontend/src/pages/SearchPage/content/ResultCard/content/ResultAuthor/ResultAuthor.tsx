import s from "./ResultAuthor.module.scss";
import LangLogo from "../../../../../../components/ui/LangLogo/LangLogo.tsx";
import { ResultAuthorData } from "../../../../../../store/slices/mainSlice.ts";
import { CoursesIcon } from "../../../../../../assets/icons";
import { Trans } from "react-i18next";

const ResultAuthor = ({
  data: { language, name, photo, courses_count },
}: {
  data: ResultAuthorData;
}) => {
  const iconCountTemplate = () =>
    !!courses_count && (
      <div className={s.icon_count_container}>
        <CoursesIcon className={s.icon} />
        <Trans i18nKey="professor.coursesCount" count={courses_count} />
      </div>
    );

  return (
    <>
      {photo ? (
        <img className={s.photo} src={photo} alt="author photo" />
      ) : (
        <div className={s.photo}></div>
      )}
      <div>
        <div className={s.card_body}>
          <p className={s.name_lang_container}>
            <LangLogo lang={language} />
            {name}
          </p>
          {iconCountTemplate()}
        </div>
      </div>
    </>
  );
};

export default ResultAuthor;
