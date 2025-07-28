import s from "./Professors.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ProfessorsList from "../../../../components/CommonComponents/ProfessorsList/ProfessorsList.tsx";

const Professors = ({ data }: { data: any }) => {
  return (
    <div id={"course-professors"} className={s.professors_container}>
      <SectionHeader name={"professors"} />
      <ProfessorsList source={"landing"} professors={data} />
    </div>
  );
};

export default Professors;
