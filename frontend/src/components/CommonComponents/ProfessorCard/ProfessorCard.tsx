import s from "./ProfessorCard.module.scss";
import ViewLink from "../../ui/ViewLink/ViewLink.tsx";
import { Link } from "react-router-dom";
import INITIAL_PHOTO from "../../../assets/no-pictures.png";

const ProfessorCard = ({
  variant,
  name,
  photo,
  description,
  link,
}: {
  variant: "vertical" | "horizontal";
  name: string;
  photo: string;
  description: string;
  link: string;
}) => {
  return (
    <Link to={link} className={s.card_wrapper}>
      <div className={s.card_header}>
        <h6>{name}</h6>
      </div>
      <div className={s.professor_card}>
        <div
          style={{
            flexDirection: `${variant === "horizontal" ? "row" : "column"}`,
          }}
          className={s.card_content}
        >
          <div className={s.photo_wrapper}>
            <img src={photo ? photo : INITIAL_PHOTO} alt="professor photo" />
          </div>
          <div className={s.description_wrapper}>
            {/*<span>*/}
            {/*  <span className={"highlight"}>*/}
            {/*    <Trans i18nKey={"professor.specialization"} />*/}
            {/*  </span>{" "}*/}
            {/*  orthodontics*/}
            {/*</span>*/}
            {/*<span>*/}
            {/*  <span className={"highlight"}>*/}
            {/*    <Trans i18nKey={"professor.coursesCount"} />*/}
            {/*  </span>{" "}*/}
            {/*  13 courses*/}
            {/*</span>*/}
            <p className={s.description}>{description}</p>
            <ViewLink className={s.professor_link} text={"professor.about"} />
          </div>
        </div>
      </div>
    </Link>
  );
};

export default ProfessorCard;
