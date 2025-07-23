import { useEffect, useRef, useState } from "react";
import s from "./TimerBanner.module.scss";
import { Trans } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import Timer from "./Timer/Timer.tsx";
import { openPaymentModal } from "../../../store/slices/paymentSlice.ts";

const TimerBanner = () => {
  const [showSticky, setShowSticky] = useState(false);
  const [renderSticky, setRenderSticky] = useState(false);
  const [discount, setDiscount] = useState(0);
  const bannerRef = useRef<HTMLDivElement | null>(null);
  const dispatch = useDispatch<AppDispatchType>();
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

  const renderBanner = (isSticky = false, isHiding = false) => (
    <div
      ref={!isSticky ? bannerRef : null}
      onClick={() => dispatch(openPaymentModal())}
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
