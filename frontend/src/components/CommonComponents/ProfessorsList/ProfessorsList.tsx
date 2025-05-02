import s from "./ProfessorsList.module.scss";
import ProfessorCard from "../ProfessorCard/ProfessorCard.tsx";
import { Path } from "../../../routes/routes.ts";
import LoaderOverlay from "../../ui/LoaderOverlay/LoaderOverlay.tsx";
import { Trans } from "react-i18next";

type Professor = {
  name: string;
  photo: string;
  description: string;
};

type props = {
  professors: Professor[];
  loading?: boolean;
};

const ProfessorsList = ({ professors, loading }: props) => {
  return (
    <div className={s.list_wrapper}>
      {loading && <LoaderOverlay />}
      {professors.length > 0 ? (
        <ul
          className={s.list}
          style={{
            display: `${professors.length <= 1 ? "flex" : "grid"}`,
            gridTemplateColumns: "repeat(2, 1fr)",
          }}
        >
          {professors.map((professor: any) => (
            <li key={professor.id}>
              <ProfessorCard
                name={professor.name}
                photo={professor.photo}
                description={professor.description}
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
