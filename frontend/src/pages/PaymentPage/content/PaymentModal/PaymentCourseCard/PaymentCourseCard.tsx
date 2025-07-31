import s from "./PaymentCourseCard.module.scss";
import { Trans } from "react-i18next";

const PaymentCourseCard = ({
  course: { newPrice, oldPrice, name, lessonsCount, img },
  isWebinar,
  isFree,
}: {
  course: {
    newPrice: number;
    oldPrice: number;
    name: string;
    lessonsCount: string;
    img: string;
  };
  isWebinar: boolean;
  isFree: boolean;
}) => {
  return (
    <div className={s.course}>
      <p>
        <img src={img} alt="" />
        {name}{" "}
        {!isWebinar && lessonsCount && (
          <>
            - <span className={"highlight"}>{lessonsCount}</span>
          </>
        )}
      </p>
      {!isFree ? (
        <div className={s.course_prices}>
          <span className={"highlight"}>${newPrice}</span>
          <span className={"crossed"}>${oldPrice}</span>
        </div>
      ) : (
        <p className={s.free_text}>
          <Trans i18nKey={"firstFreeLesson"} />
        </p>
      )}
    </div>
  );
};

export default PaymentCourseCard;
