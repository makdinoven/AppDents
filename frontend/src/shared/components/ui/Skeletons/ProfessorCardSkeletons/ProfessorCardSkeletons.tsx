import React from "react";
import s from "./ProfessorCardSkeletons.module.scss";

interface ProfessorCardSkeletonsProps {
  amount?: number;
}

const ProfessorCardSkeletons: React.FC<ProfessorCardSkeletonsProps> = ({
  amount = 12,
}: ProfessorCardSkeletonsProps) => {
  const skeletonsList = Array(amount).fill({ length: amount });

  return (
    <ul className={`${s.skeletons}`}>
      {skeletonsList.map((_, index) => (
        <li key={index} className={s.card_wrapper}>
          <div className={s.card_header}>
            <h6></h6>
          </div>
          <div className={s.professor_card}>
            <div className={s.card_content}>
              <div className={s.photo_wrapper}>
                <div></div>
              </div>
              <div className={s.description_wrapper}>
                <div className={s.courses_count}></div>
                <p className={s.description}></p>
              </div>
              <div className={s.professor_link}></div>
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
};

export default ProfessorCardSkeletons;
