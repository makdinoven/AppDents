import React from "react";
import s from "./ProfileMainSkeleton.module.scss";

const ProfileMainSkeleton: React.FC = () => {
  return (
    <div className={s.skeleton}>
      <div className={s.user_info}>
        <div className={s.left}>
          <div className={s.user_top}>
            <div className={s.user_items}>
              <div className={s.mail}></div>
              <div className={s.support}></div>
            </div>
          </div>
          <div className={s.profile_buttons}></div>
        </div>
        <div className={s.referral_section}>
          <div className={s.content_body}>
            <div className={s.balance}></div>
            <div className={s.button}></div>
          </div>
          <div className={s.text}></div>
          <div className={s.content_bottom}>
            <div className={s.link}></div>
            <div className={s.copy}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileMainSkeleton;
