import s from "./Offer.module.scss";
import CircleArrow from "../../../../common/Icons/CircleArrow.tsx";
import { Trans } from "react-i18next";
import Clock from "../../../../common/Icons/Clock.tsx";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";

const Offer = ({ data }: { data: any }) => {
  return (
    <section>
      <div className={s.offer_card}>
        <div className={s.card_header}>
          <div className={s.card_header_text}>
            <Trans i18nKey="landing.specialOffer" />
          </div>
          <div className={s.card_header_background}></div>
        </div>
        <div className={s.card_body}>
          <div className={s.content}>
            <h6>{data.landing_name}</h6>
            <p>{data.authors}</p>
            <div className={s.line_arrow}>
              <span></span>
              <CircleArrow />
            </div>
          </div>
          <div className={s.card_bottom}>
            <div className={s.card_bottom_content}>
              <Clock />
              <Trans i18nKey="landing.accessFull"></Trans>
            </div>

            <ArrowButton>
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
            </ArrowButton>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Offer;
