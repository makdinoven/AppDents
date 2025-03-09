import s from "./Professors.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";

const Professors = ({ data }: { data: any }) => {
  return (
    <div className={s.professors_container}>
      <SectionHeader name={"landing.professors"} />
      <ul>
        {data.map((professor: any) => (
          <li className={s.professor_card} key={professor.id}>
            <div className={s.photo_wrapper}>
              <img src={professor.photo} alt="photo" />
            </div>
            <div className={s.professor_text}>
              <h6> {professor.name}</h6>
              <p>{professor.description}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Professors;
