import s from "./ProfessorsList.module.scss";
import ProfessorCard from "../ProfessorCard/ProfessorCard.tsx";
import { Trans } from "react-i18next";
import { PATHS } from "../../../app/routes/routes.ts";
import LoaderOverlay from "../ui/LoaderOverlay/LoaderOverlay.tsx";

type Professor = {
  id: number;
  name: string;
  photo: string;
  description: string;
  tags: string[];
  courses_count: number;
  books_count: number;
};

type props = {
  professors: Professor[];
  loading?: boolean;
  showLoaderOverlay?: boolean;
};

const ProfessorsList = ({ professors, loading, showLoaderOverlay }: props) => {
  return (
    <div className={s.list_wrapper}>
      {showLoaderOverlay && <LoaderOverlay />}
      {professors.length > 0 ? (
        <ul className={s.list}>
          {professors.map((professor) => (
            <li key={professor.id}>
              <ProfessorCard
                name={professor.name}
                photo={professor.photo}
                description={professor.description}
                tags={professor.tags}
                books_count={professor.books_count}
                courses_count={professor.courses_count}
                link={PATHS.PROFESSOR_PAGE.build(professor.id.toString())}
              />
            </li>
          ))}
        </ul>
      ) : (
        !loading && (
          <p className={s.no_professors}>
            <Trans i18nKey={"professor.noProfessors"} />
          </p>
        )
      )}
    </div>
  );
};

export default ProfessorsList;
