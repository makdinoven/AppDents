import s from "./Professors.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";

const Professors = ({ data }: { data: any }) => {
  const professors = data;

  return (
    <div className={s.professors_container}>
      <SectionHeader name={"professors"} />
      <ul style={{ display: `${professors.length <= 1 ? "flex" : "grid"}` }}>
        {professors.map((professor: any) => (
          <li className={s.professor_card} key={professor.id}>
            <div className={s.photo_wrapper}>
              <img src={professor.photo ? professor.photo : null} alt="photo" />
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
