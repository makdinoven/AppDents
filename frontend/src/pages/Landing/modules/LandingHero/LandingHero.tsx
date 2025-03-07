import s from "./LandingHero.module.scss";
import Title from "../../../../components/CommonComponents/Title/Title.tsx";
import { Trans } from "react-i18next";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import CircleArrow from "../../../../common/Icons/CircleArrow.tsx";
import initialPhoto from "../../../../assets/no-pictures.png";

const LandingHero = ({ data }: { data: any }) => {
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
              {data.photo ? (
                <img src={data.photo} alt="Course image" />
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
          <h2>{data.landing_name}</h2>
          <div className={s.arrow}>
            <CircleArrow />
          </div>
          <p>{data.authors}</p>
          <ArrowButton>
            <span>
              <Trans
                i18nKey="landing.buyFor"
                values={{
                  new_price: data.new_price,
                  old_price: data.old_price,
                }}
                components={{
                  1: <span className="crossed" />,
                  2: <span className="highlight" />,
                }}
              />
            </span>
          </ArrowButton>
        </div>
      </div>
    </section>
  );
};

export default LandingHero;
