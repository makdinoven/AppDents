import { Link } from "react-router-dom";
import s from "./Slide.module.scss";
import { Path } from "../../../../routes/routes";
import PrettyButton from "../../../ui/PrettyButton/PrettyButton";
import { Authors, CoursesIcon } from "../../../../assets/icons";
import { useTranslation } from "react-i18next";
import noPictures from "@/assets/no-pictures.png";
import { capitalizeText } from "../../../../common/helpers/helpers";

interface SlideProps {
  slideInfo: any;
}

const Slide = ({ slideInfo }: SlideProps) => {
  console.log(slideInfo);
  const { t } = useTranslation();

  const authors =
    slideInfo.landing?.authors?.map((author: any) => author.name) || [];

  return (
    <div className={s.slide}>
      <Link to={Path.courses}>
        <div className={s.slide_photo}>
          <img
            src={slideInfo.landing?.main_image || noPictures}
            alt="Course cover"
          />
        </div>
        <div className={s.slide_content}>
          <div className={s.slide_widgets}>
            <div className={s.type}>
              <CoursesIcon />
              <span>{slideInfo.type}</span>
            </div>
            <div className={s.price}>
              ${slideInfo.landing?.new_price}
              <span>${slideInfo.landing?.old_price}</span>
            </div>
          </div>
          <h2>{slideInfo.landing?.landing_name}</h2>
          <p className={s.course_content}>{slideInfo.landing?.lessons_count}</p>
          <p className={s.course_description}>
            {slideInfo.landing?.description ||
              "Lorem ipsum dolor sit amet consectetur. Id ut in praesent eu velit integer praesent suspendisse egestas. Enim egestas pellentesque leo."}
          </p>
          <div className={s.slide_footer}>
            <div className={s.course_authors}>
              <Authors />
              <p>
                {t("landing.by")} {capitalizeText(authors.join(", "))}{" "}
                {t("etAl")}
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
