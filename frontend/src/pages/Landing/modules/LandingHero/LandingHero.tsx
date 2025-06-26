import s from "./LandingHero.module.scss";
import Title from "../../../../components/ui/Title/Title.tsx";
import { Trans } from "react-i18next";
import initialPhoto from "../../../../assets/no-pictures.png";
import CircleArrow from "../../../../assets/Icons/CircleArrow.tsx";

const LandingHero = ({
  type = "video",
  data: { photo, landing_name, authors, renderBuyButton },
}: {
  type?: "book" | "video";
  data: any;
}) => {
  const isBook = type === "book";

  const renderLandingTitle = () => {
    if (isBook) {
      return (
        <Title>
          <Trans i18nKey={"bookLanding.onlineBook"} />
        </Title>
      );
    } else {
      return (
        <Title>
          <Trans i18nKey={"onlineCourse"} />
        </Title>
      );
    }
  };

  return (
    <section className={s.hero}>
      <div className={s.hero_top}>
        {renderLandingTitle()}
        <div className={`${s.card_header} ${isBook ? s.book : ""}`}></div>
      </div>

      <div className={s.hero_content_wrapper}>
        <div className={`${s.card} ${isBook ? s.book : ""}`}>
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
