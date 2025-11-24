import s from "./ProfilePage.module.scss";
import { NavLink, Outlet } from "react-router-dom";
import BackButton from "../../../shared/components/ui/BackButton/BackButton.tsx";
import { t } from "i18next";
import { PATHS } from "../../../app/routes/routes.ts";

const ProfilePage = () => {
  const tabs: { path: string; title: string }[] = [
    { path: PATHS.PROFILE, title: "profile.main" },
    { path: PATHS.PROFILE_MY_COURSES, title: "profile.yourCourses" },
    { path: PATHS.PROFILE_MY_BOOKS, title: "profile.yourBooks" },
    {
      path: PATHS.PROFILE_PURCHASE_HISTORY,
      title: "profile.purchaseHistory.purchases",
    },
    {
      path: PATHS.PROFILE_INVITED_USERS,
      title: "profile.purchaseHistory.invitedUsers",
    },
  ];

  return (
    <>
      <BackButton />
      <div className={s.btns_container}>
        {tabs.map((tab) => {
          const isFull = tab.path === PATHS.PROFILE ? s.full : "";
          return (
            <NavLink
              key={tab.path}
              to={tab.path}
              className={({ isActive }) =>
                `${s.btn} ${isActive ? s.active : ""} ${isFull}`
              }
            >
              {t(tab.title)}
            </NavLink>
          );
        })}
      </div>
      <Outlet />
    </>
  );
};

export default ProfilePage;
