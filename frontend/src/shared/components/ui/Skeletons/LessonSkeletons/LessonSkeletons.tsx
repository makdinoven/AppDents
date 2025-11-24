import React from "react";
import s from "./LessonSkeletons.module.scss";

interface LessonSkeletonsProps {
  amount?: number;
}

const LessonSkeletons: React.FC<LessonSkeletonsProps> = ({
  amount = 4,
}: LessonSkeletonsProps) => {
  const skeletonsList = Array(amount).fill({ length: amount });

  return (
    <ul className={s.skeletons}>
      {skeletonsList.map((_, index) => {
        return (
          <li key={index} className={s.card}>
            <div className={s.card_content}>
              <h3></h3>
              <div></div>
            </div>
            <div className={s.photo}></div>
          </li>
        );
      })}
    </ul>
  );
};

export default LessonSkeletons;
