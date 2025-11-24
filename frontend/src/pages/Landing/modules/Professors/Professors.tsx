import s from "./Professors.module.scss";
import SectionHeader from "../../../../shared/components/ui/SectionHeader/SectionHeader.tsx";
import ProfessorsList from "../../../../shared/components/ProfessorsList/ProfessorsList.tsx";

const Professors = ({ data }: { data: any }) => {
  return (
    <div id={"course-professors"} className={s.professors_container}>
      <SectionHeader name={"professors"} />
      <ProfessorsList professors={data} />
    </div>
  );
};

export default Professors;
