import s from "./ProfessorsList.module.scss";
import ProfessorCard from "../ProfessorCard/ProfessorCard.tsx";
import { Path } from "../../../routes/routes.ts";

type Professor = {
  name: string;
  photo: string;
  description: string;
};

const ProfessorsList = ({ professors }: { professors: Professor[] }) => {
  return (
    <ul
      className={s.list}
      style={{
        display: `${professors.length <= 1 ? "flex" : "grid"}`,
        gridTemplateColumns: ` ${professors.length === 2 ? "repeat(2, 1fr)" : "repeat(3, 1fr)"}`,
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
  );
};

export default ProfessorsList;
