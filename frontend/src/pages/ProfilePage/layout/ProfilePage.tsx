import s from "./ProfilePage.module.scss";
import { NavLink, Outlet } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";
import BackButton from "../../../components/ui/BackButton/BackButton.tsx";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { t } from "i18next";

const ProfilePage = () => {
  const screenWidth = useScreenWidth();

  return (
    <>
      <div className={s.back_btn_tabs_container}>
        {screenWidth > 576 && <BackButton />}
        <div className={s.btns_container}>
          <NavLink
            to={Path.profileMain}
            className={({ isActive }) =>
              isActive ? `${s.btn} ${s.active}` : s.btn
            }
          >
            {t("profile.main")}
          </NavLink>
          <NavLink
            to={Path.yourCourses}
            className={({ isActive }) =>
              isActive ? `${s.btn} ${s.active}` : s.btn
            }
          >
            {t("profile.yourCourses")}
          </NavLink>
          <NavLink
            to={Path.yourBooks}
            className={({ isActive }) =>
              isActive ? `${s.btn} ${s.active}` : s.btn
            }
          >
            {t("profile.yourBooks")}
          </NavLink>
          <NavLink
            to={Path.purchaseHistory}
            className={({ isActive }) =>
              isActive ? `${s.btn} ${s.active}` : s.btn
            }
          >
            {t("profile.purchaseHistory.purchases")}
          </NavLink>
        </div>
      </div>
      <div className={s.profile_page}>
        <Outlet />
      </div>
    </>
  );
};

export default ProfilePage;
