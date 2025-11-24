import React from "react";
import s from "./BookCardSkeletons.module.scss";

interface BookCardSkeletonsProps {
  amount?: number;
  moveUp?: boolean;
  fade?: boolean;
}

const BookCardSkeletons: React.FC<BookCardSkeletonsProps> = ({
  amount = 4,
  moveUp = false,
  fade = false,
}: BookCardSkeletonsProps) => {
  const skeletonsList = Array(amount).fill({ length: amount });

  return (
    <ul
      className={`${s.skeletons} ${moveUp ? s.no_margin : ""} ${fade ? s.fade : ""}`}
    >
      {skeletonsList.map((_, index) => {
        return (
          <li key={index} className={s.card}>
            <div className={s.card_header}>
              <div className={s.photo} />
            </div>
            <div className={s.card_body}>
              <h4 />
              <ul className={s.formats}>
                {Array(5)
                  .fill({ length: 5 })
                  .map((_, index) => (
                    <li key={index} />
                  ))}
              </ul>
              <div />
            </div>
            <div className={s.card_bottom}>
              <div className={s.buy} />
              <div className={s.cart} />
            </div>
          </li>
        );
      })}
    </ul>
  );
};

export default BookCardSkeletons;
