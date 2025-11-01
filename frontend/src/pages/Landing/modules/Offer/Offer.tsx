import s from "./Offer.module.scss";
import { CircleArrow, Lightning } from "../../../../assets/icons";
import { Trans } from "react-i18next";
import { Clock } from "../../../../assets/icons";

const Offer = ({
  data: { landing_name, authors, renderBuyButton, isWebinar },
}: {
  data: any;
}) => {
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
            <h6>{landing_name}</h6>
            <p>{authors}</p>
            <div className={s.line_arrow}>
              <span></span>
              <CircleArrow />
            </div>
          </div>
          <div className={s.card_bottom}>
            <div className={s.card_bottom_content}>
              <span>
                <Lightning className={s.lightning} />
              </span>
              <p>
                <Trans
                  i18nKey={
                    isWebinar
                      ? "landing.instantAccessFullWebinar"
                      : "landing.instantAccessFull"
                  }
                ></Trans>
              </p>
            </div>
            <div className={s.card_bottom_content}>
              <span>
                <Clock />
              </span>
              <p>
                <Trans
                  i18nKey={
                    isWebinar
                      ? "landing.accessFullWebinar"
                      : "landing.accessFull"
                  }
                ></Trans>
              </p>
            </div>

            {renderBuyButton}
          </div>
        </div>
      </div>
    </section>
  );
};

export default Offer;
