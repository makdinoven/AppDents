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
    <div className={`${s.course} ${isFree ? s.free : ""}`}>
      <img src={img} alt="" />

      <div className={s.course_info}>
        {!isWebinar && lessonsCount && (
          <p className={s.lessons_count}>{lessonsCount}</p>
        )}
        <h4 className={s.course_name}>{name}</h4>
      </div>

      {!isFree ? (
        <div className={s.course_prices}>
          <span className={s.new_price}>${newPrice}</span>
          <span className={s.old_price}>${oldPrice}</span>
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
