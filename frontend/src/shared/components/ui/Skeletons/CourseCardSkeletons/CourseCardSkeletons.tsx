import React from "react";
import s from "./CourseCardSkeletons.module.scss";

interface CourseCardSkeletonsProps {
  shape?: boolean;
  amount?: number;
  columns?: number;
  moveUp?: boolean;
  fade?: boolean;
}

const CourseCardSkeletons: React.FC<CourseCardSkeletonsProps> = ({
  shape = false,
  amount = 4,
  columns = 2,
  moveUp = false,
  fade = false,
}: CourseCardSkeletonsProps) => {
  const skeletonsList = Array(amount).fill({ length: amount });

  return (
    <ul
      className={`${s.skeletons} ${shape ? s.shape : ""} ${moveUp ? s.no_margin : ""} ${fade ? s.fade : ""}`}
      style={{ "--columns": columns } as React.CSSProperties}
    >
      {skeletonsList.map((_, index) => {
        return shape ? (
          <li key={index} className={`${s.card} ${s.shape}`}>
            <div className={`${s.card_header} ${s.shape}`}></div>
            <div className={s.card_body}>
              <div className={s.card_content_header}>
                <div className={s.prices}></div>
                <p className={s.lessons_count}></p>
              </div>
              <div className={s.card_content_body}>
                <div className={s.authors}></div>
                <div className={s.content_bottom}>
                  <div className={s.photo}></div>
                </div>
                <div className={`${s.buttons}`}>
                  <div className={s.buy}></div>
                  <div className={s.cart}></div>
                </div>
              </div>
            </div>
            <div className={`${s.card_bottom} ${s.shape}`}></div>
          </li>
        ) : (
          <li key={index} className={s.card}>
            <div className={s.card_content}>
              <h3></h3>
              <div></div>
            </div>
            <div className={s.card_bottom_shapeless}>
              <div className={s.buttons_shapeless}></div>
            </div>
          </li>
        );
      })}
    </ul>
  );
};

export default CourseCardSkeletons;
