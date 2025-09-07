import s from "./ProfessorsList.module.scss";
import ProfessorCard from "../ProfessorCard/ProfessorCard.tsx";
import { Path } from "../../../routes/routes.ts";
import { Trans } from "react-i18next";

type Professor = {
  id: number;
  name: string;
  photo: string;
  description: string;
  tags: string[];
  courses_count: number;
};

type props = {
  professors: Professor[];
  source: "page" | "landing";
  loading?: boolean;
};

const ProfessorsList = ({ professors, loading, source }: props) => {
  const getGridTemplateColumns = (count: number) => {
    if (count === 3) return "repeat(3, 1fr)";
    if (count === 2) return "repeat(2, 1fr)";
    if (count === 1) return "repeat(1, 1fr)";
    return "repeat(4, 1fr)";
  };

  return (
    <div className={s.list_wrapper}>
      {/*{loading && <LoaderOverlay />}*/}
      {professors.length > 0 ? (
        <ul
          style={{
            gridTemplateColumns: `${getGridTemplateColumns(professors.length)}`,
          }}
          className={`${s.list} ${s[source]}`}
        >
          {professors.map((professor) => (
            <li key={professor.id}>
              <ProfessorCard
                variant={professors.length < 2 ? "horizontal" : "vertical"}
                name={professor.name}
                photo={professor.photo}
                description={professor.description}
                tags={professor.tags}
                courses_count={professor.courses_count}
                link={`${Path.professor}/${professor.id}`}
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
