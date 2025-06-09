import { forwardRef } from "react";
import s from "./TimerBanner.module.scss";
import CountdownTimer from "../CountdownTimer/CountdownTimer.tsx";
import { Trans } from "react-i18next";
import Clock from "../../../assets/Icons/Clock.tsx";

const TimerBanner = forwardRef<
  HTMLDivElement,
  {
    discount: number;
    onClick: () => void;
    isSticky?: boolean;
    isHiding?: boolean;
  }
>(({ onClick, isSticky, isHiding, discount }, ref) => {
  return (
    <div
      ref={ref}
      onClick={onClick}
      className={`${s.banner} ${isSticky ? s.sticky : ""} ${isHiding ? s.hiding : ""}`}
    >
      <div className={s.banner_container}>
        <div className={s.banner_content}>
          <div className={s.timer}>
            <Clock />
            <CountdownTimer />
          </div>
          <h4>
            <Trans
              i18nKey={"banner.title"}
              values={{ discount: discount }}
              components={{
                1: <span className={s.highlight_text}></span>,
              }}
            />
          </h4>
        </div>
      </div>
    </div>
  );
});

export default TimerBanner;
