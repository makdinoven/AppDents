import s from "./ProfilePage.module.scss";
import { NavLink, Outlet } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import BackButton from "../../../components/ui/BackButton/BackButton.tsx";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { t } from "i18next";

const ProfilePage = () => {
  const screenWidth = useScreenWidth();

  const tabs: { path: string; title: string }[] = [
    { path: Path.profileMain, title: "profile.main" },
    { path: Path.yourCourses, title: "profile.yourCourses" },
    { path: Path.yourBooks, title: "profile.yourBooks" },
    {
      path: Path.purchaseHistory,
      title: "profile.purchaseHistory.purchases",
    },
    {
      path: Path.invitedUsers,
      title: "profile.purchaseHistory.invitedUsers",
    },
  ];

  return (
    <>
      <div className={s.back_btn_tabs_container}>
        {screenWidth > 576 && <BackButton />}
        <div className={s.btns_container}>
          {tabs.map((tab) => {
            const isFull = tab.path === Path.profileMain ? s.full : "";
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
      </div>
      <Outlet />
    </>
  );
};

export default ProfilePage;
