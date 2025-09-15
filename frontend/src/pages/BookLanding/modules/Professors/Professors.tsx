import s from "./Professors.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ProfessorsList from "../../../../components/CommonComponents/ProfessorsList/ProfessorsList.tsx";

interface ProfessorsProps {
  professors: any[];
}

const Professors = ({ professors }: ProfessorsProps) => {
  return (
    <div id={"course-professors"} className={s.professors_container}>
      <SectionHeader name={"professors"} />
      <ProfessorsList source={"landing"} professors={professors} />
    </div>
  );
};

export default Professors;
