import { useEffect, useRef, useState } from "react";
import s from "./TimerBanner.module.scss";
import { Trans } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { openModal } from "../../../store/slices/landingSlice.ts";
import Timer from "./Timer/Timer.tsx";

const TimerBanner = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const [showSticky, setShowSticky] = useState(false);
  const [renderSticky, setRenderSticky] = useState(false);
  const bannerRef = useRef<HTMLDivElement | null>(null);

  const oldPrice = useSelector(
    (state: AppRootStateType) => state.landing.oldPrice,
  );
  const newPrice = useSelector(
    (state: AppRootStateType) => state.landing.newPrice,
  );

  const discount = Number(
    (((oldPrice - newPrice) / oldPrice) * 100).toFixed(0),
  );

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) {
          setRenderSticky(true);
          setShowSticky(true);
        } else {
          setShowSticky(false);
          setTimeout(() => setRenderSticky(false), 300);
        }
      },
      { threshold: 0 },
    );

    if (bannerRef.current) observer.observe(bannerRef.current);

    return () => {
      if (bannerRef.current) observer.unobserve(bannerRef.current);
    };
  }, []);

  const handleClick = () => {
    dispatch(openModal());
  };

  const renderBanner = (isSticky = false, isHiding = false) => (
    <div
      ref={!isSticky ? bannerRef : null}
      onClick={handleClick}
      className={`${s.banner} ${isSticky ? s.sticky : ""} ${isHiding ? s.hiding : ""}`}
    >
      <div className={s.banner_container}>
        <Timer />
        <h4>
          <Trans
            i18nKey={"banner.title"}
            values={{ discount: discount ? discount : 90 }}
            components={{ 1: <span className={s.highlight_text} /> }}
          />
        </h4>
      </div>
    </div>
  );

  return (
    <>
      {renderBanner(false)}
      {renderSticky && renderBanner(true, !showSticky)}
    </>
  );
};

export default TimerBanner;
