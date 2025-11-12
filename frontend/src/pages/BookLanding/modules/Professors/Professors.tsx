import s from "./Professors.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import ProfessorsList from "../../../../components/CommonComponents/ProfessorsList/ProfessorsList.tsx";

interface ProfessorsProps {
  professors: any[];
  type?: "course" | "book";
}

const Professors = ({ professors, type = "course" }: ProfessorsProps) => {
  return (
    <div
      id={type === "book" ? "book-authors" : "course-professors"}
      className={s.professors_container}
    >
      <SectionHeader name={"professors"} />
      <ProfessorsList professors={professors} />
    </div>
  );
};

export default Professors;
