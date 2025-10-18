import s from "./PaymentItemCard.module.scss";
import { Trans } from "react-i18next";
import {
  CartItemBookType,
  CartItemCourseType,
  CartItemKind,
} from "../../../../api/cartApi/types.ts";

const PaymentItemCard = ({
  item,
  isWebinar,
  isFree,
  language,
  itemType,
}: {
  item: CartItemCourseType | CartItemBookType;
  itemType: CartItemKind;
  language: string;
  isWebinar: boolean;
  isFree: boolean;
}) => {
  const { new_price, old_price, landing_name, preview_photo } = item;
  const lessons_count =
    "lessons_count" in item ? item.lessons_count : undefined;

  return (
    <div
      className={`${s.course} ${isFree ? s.free : ""} ${itemType === "BOOK" ? s.book : ""}`}
    >
      <div
        className={`${s.img_wrapper} ${!preview_photo ? s.no_photo : ""} ${s[itemType.toLowerCase()]}`}
      >
        {preview_photo && <img src={preview_photo} alt={`${itemType} photo`} />}
      </div>

      <div className={s.course_info}>
        {!isWebinar && lessons_count && (
          <p className={s.lessons_count}>{lessons_count}</p>
        )}
        <h4 lang={language.toLowerCase()} className={s.course_name}>
          {landing_name}
        </h4>
      </div>

      {!isFree ? (
        <div className={s.course_prices}>
          <span className={s.new_price}>${new_price}</span>
          <span className={s.old_price}>${old_price}</span>
        </div>
      ) : (
        <p className={s.free_text}>
          <Trans i18nKey={"firstFreeLesson"} />
        </p>
      )}
    </div>
  );
};

export default PaymentItemCard;
