import s from "../Header.module.scss";
import Timer from "../../ui/TimerBanner/Timer/Timer.tsx";
import { openModal } from "../../../store/slices/landingSlice.ts";
import { Trans } from "react-i18next";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";

const VideoHeaderContent = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const oldPrice = useSelector(
    (state: AppRootStateType) => state.landing.oldPrice,
  );
  const newPrice = useSelector(
    (state: AppRootStateType) => state.landing.newPrice,
  );
  const lessonsCount = useSelector(
    (state: AppRootStateType) => state.landing.lessonsCount,
  );

  function extractMaxNumber(text: string) {
    const matches = text.match(/\d+/g);
    if (!matches) return 0;

    const numbers = matches.map(Number);
    return Math.max(...numbers);
  }

  const lessonsCountNumber = extractMaxNumber(lessonsCount);

  return (
    <div className={s.video_content}>
      {!!oldPrice && !!newPrice && (
        <>
          <Timer appearance={"primary"} />
          <button
            onClick={() => dispatch(openModal())}
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
