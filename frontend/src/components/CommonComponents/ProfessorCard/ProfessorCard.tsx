import s from "./ProfessorCard.module.scss";
import ViewLink from "../../ui/ViewLink/ViewLink.tsx";
import { Link } from "react-router-dom";

const ProfessorCard = ({
  name,
  photo,
  description,
  link,
}: {
  name: string;
  photo: string;
  description: string;
  link: string;
}) => {
  return (
    <Link to={link} className={s.card_wrapper}>
      <div className={s.card_header}>
        <h6> {name}</h6>
      </div>
      <div className={s.professor_card}>
        <div className={s.card_content}>
          {photo && (
            <div className={s.photo_wrapper}>
              <img src={photo} alt="photo" />
            </div>
          )}

          <p className={s.description}>{description}</p>
        </div>

        <ViewLink text={"about_professor"} />
      </div>
    </Link>
  );
};

export default ProfessorCard;
