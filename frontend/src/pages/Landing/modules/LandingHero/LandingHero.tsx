import s from "./LandingHero.module.scss";
import Title from "../../../../components/ui/Title/Title.tsx";
import { Trans } from "react-i18next";
import initialPhoto from "../../../../assets/no-pictures.png";
import CircleArrow from "../../../../assets/icons/CircleArrow.tsx";

const LandingHero = ({
  data: { photo, landing_name, authors, renderBuyButton },
}: {
  data: any;
}) => {
  return (
    <section className={s.hero}>
      <div className={s.hero_top}>
        <Title>
          <Trans i18nKey={"onlineCourse"} />
        </Title>
        <div className={s.card_header}></div>
      </div>

      <div className={s.hero_content_wrapper}>
        <div className={s.card}>
          <div className={s.card_body}>
            <div className={s.photo}>
              {photo ? (
                <img src={photo} alt="Course image" />
              ) : (
                <div
                  style={{ backgroundImage: `url(${initialPhoto})` }}
                  className={s.no_photo}
                ></div>
              )}
            </div>
          </div>
          <div className={s.card_bottom}></div>
        </div>

        <div className={s.hero_content}>
          <h2>{landing_name}</h2>
          <div className={s.arrow}>
            <CircleArrow />
          </div>
          <p>{authors}</p>
          {renderBuyButton}
        </div>
      </div>
    </section>
  );
};

export default LandingHero;
