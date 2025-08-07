import { Link } from "react-router-dom";
import s from "./Slide.module.scss";
import { Path } from "../../../../routes/routes";
import PrettyButton from "../../../ui/PrettyButton/PrettyButton";
import { Authors, CoursesIcon } from "../../../../assets/icons";
import { useTranslation } from "react-i18next";

interface SlideProps {
  slideInfo: any;
}

const Slide = ({ slideInfo }: SlideProps) => {
  const { t } = useTranslation();
  return (
    <div className={s.slide}>
      <Link to={Path.courses}>
        <div className={s.slide_photo}>
          <img src={slideInfo.photo} alt="Course cover" />
        </div>
        <div className={s.slide_content}>
          <div className={s.slide_widgets}>
            <div className={s.type}>
              <CoursesIcon />
              <span>{slideInfo.type}</span>
            </div>
            <div className={s.price}>
              ${slideInfo.newPrice}
              <span>${slideInfo.oldPrice}</span>
            </div>
          </div>
          <h2>{slideInfo.name}</h2>
          <p className={s.course_content}>{slideInfo.lessonsCount}</p>
          <p className={s.course_description}>{slideInfo.description}</p>
          <div className={s.slide_footer}>
            <div className={s.course_authors}>
              <Authors />
              <p>
                {t("landing.by")} {slideInfo.authors.join(", ")} {t("etAl")}
              </p>
            </div>
            <PrettyButton
              text="Buy"
              variant="primary"
              className={s.buy_button}
            />
          </div>
        </div>
      </Link>
    </div>
  );
};

export default Slide;
