import s from "../Header.module.scss";
import Timer from "../../ui/TimerBanner/Timer/Timer.tsx";
import { Trans } from "react-i18next";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import { usePaymentPageHandler } from "../../../common/hooks/usePaymentPageHandler.ts";

const VideoHeaderContent = () => {
  const { openPaymentModal } = usePaymentPageHandler();
  const oldPrice = useSelector(
    (state: AppRootStateType) => state.payment.data?.old_price,
  );
  const newPrice = useSelector(
    (state: AppRootStateType) => state.payment.data?.new_price,
  );
  const lessonsCount = useSelector(
    (state: AppRootStateType) =>
      // @ts-ignore
      state.payment?.render?.items[0].data.lessons_count,
  );

  function extractMaxNumber(text: string) {
    const matches = text.match(/\d+/g);
    if (!matches) return 0;

    const numbers = matches.map(Number);
    return Math.max(...numbers);
  }

  let lessonsCountNumber;

  if (lessonsCount) {
    lessonsCountNumber = extractMaxNumber(lessonsCount);
  }

  return (
    <div className={s.video_content}>
      {!!oldPrice && !!newPrice && (
        <>
          <Timer appearance={"primary"} />
          <button
            onClick={() => openPaymentModal()}
            className={`${s.buy_btn} ${s.video}`}
          >
            <Trans
              i18nKey={"landing.buyLessonsFor"}
              values={{
                old_price: oldPrice,
                new_price: newPrice,
                count: lessonsCountNumber,
              }}
              components={{
                1: <span className="crossed-15" />,
                2: <span className="highlight" />,
              }}
            />
          </button>
        </>
      )}
    </div>
  );
};

export default VideoHeaderContent;
