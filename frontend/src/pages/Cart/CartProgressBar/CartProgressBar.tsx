import s from "./CartProgressBar.module.scss";
import { Trans } from "react-i18next";

const MIN_DISCOUNT = 0;
const MAX_DISCOUNT = 70;
const MAX_QUANTITY = 25;

type Props = {
  current_discount: number;
  next_discount: number;
  quantity: number;
};

const CartProgressBar = ({
  current_discount,
  next_discount,
  quantity,
}: Props) => {
  const fillPercent = Math.min((quantity / MAX_QUANTITY) * 100, 100);

  return (
    <div className={s.bar_container}>
      <div className={s.bar}>
        <div className={s.fill} style={{ width: `${fillPercent}%` }} />
        <div className={s.ticks}>
          {Array.from({ length: MAX_QUANTITY - quantity - 1 }).map((_, i) => {
            const step = quantity + i + 1;
            const leftPercent = (step / MAX_QUANTITY) * 100;

            return (
              <div
                key={step}
                className={s.tick}
                style={{ left: `${leftPercent}%` }}
              />
            );
          })}
        </div>
      </div>
      <div className={s.bar_percents}>
        <span className={s.min}>{MIN_DISCOUNT}%</span>
        <div className={s.discount_text}>
          <p>
            {current_discount !== next_discount ? (
              <Trans
                i18nKey={"cart.barText_1"}
                components={{
                  1: <span className={"highlight_blue_bold"}></span>,
                }}
                values={{ current: current_discount }}
              />
            ) : (
              <Trans
                i18nKey={"cart.barTextMaxDiscount"}
                components={{
                  1: <span className={"highlight_blue_bold"}></span>,
                }}
                values={{ current: current_discount }}
              />
            )}
          </p>
          {current_discount !== next_discount && (
            <p>
              <Trans
                i18nKey={"cart.barText_2"}
                components={{
                  2: <span className={"highlight_bold"}></span>,
                }}
                values={{ next: next_discount }}
              />
            </p>
          )}
        </div>
        <span className={"highlight_bold"}>{MAX_DISCOUNT}%</span>
      </div>
    </div>
  );
};

export default CartProgressBar;
