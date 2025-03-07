import s from "./Professors.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";

const Professors = ({ data }: { data: any }) => {
  console.log(data);

  return (
    <div className={s.professors_container}>
      <SectionHeader name={"landing.professors"} />
      <ul></ul>
    </div>
  );
};

export default Professors;
