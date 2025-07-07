import { useEffect, useRef, useState } from "react";
import s from "./TimerBanner.module.scss";
import { Trans } from "react-i18next";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import Timer from "./Timer/Timer.tsx";
import { useLocation, useNavigate } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";

const TimerBanner = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [showSticky, setShowSticky] = useState(false);
  const [renderSticky, setRenderSticky] = useState(false);
  const [discount, setDiscount] = useState(0);
  const bannerRef = useRef<HTMLDivElement | null>(null);
  const slug = useSelector(
    (state: AppRootStateType) => state.payment.data?.slug,
  );
  const oldPrice = useSelector(
    (state: AppRootStateType) => state.payment.data?.oldPrice,
  );
  const newPrice = useSelector(
    (state: AppRootStateType) => state.payment.data?.newPrice,
  );

  useEffect(() => {
    if (oldPrice && newPrice) {
      setDiscount(
        Number((((oldPrice - newPrice) / oldPrice) * 100).toFixed(0)),
      );
    }
  }, [oldPrice, newPrice]);

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
    navigate(`${Path.payment}/${slug}`, {
      state: { backgroundLocation: location },
    });
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
