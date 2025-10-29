import s from "./ProfilePage.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import PrettyButton from "../../../components/ui/PrettyButton/PrettyButton.tsx";
import { Path } from "../../../routes/routes.ts";
import ProductsSection from "../../../components/ProductsSection/ProductsSection.tsx";
import BackButton from "../../../components/ui/BackButton/BackButton.tsx";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { t } from "i18next";

const ProfilePage = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const navigate = useNavigate();
  const screenWidth = useScreenWidth();

  return (
    <>
      {role === "admin" && (
        <div className={s.admin_wrapper}>
          <PrettyButton
            variant="primary"
            text={"Admin panel"}
            onClick={() => navigate(Path.adminLandingListing)}
          />
        </div>
      )}
      <div className={s.back_btn_tabs_container}>
        {screenWidth > 576 && <BackButton />}

        <div className={s.btns_container}>
          <NavLink to={Path.profileMain} className={s.btn}>
            {t("profile.main")}
          </NavLink>
          <NavLink to={Path.yourCourses} className={s.btn}>
            {t("profile.yourCourses")}
          </NavLink>
          <NavLink to={Path.yourBooks} className={s.btn}>
            {t("profile.yourBooks")}
          </NavLink>
          <NavLink to={Path.purchaseHistory} className={s.btn}>
            {t("profile.purchaseHistory.purchases")}
          </NavLink>
        </div>
      </div>
      <div className={s.profilePage}>
        <Outlet />
      </div>
      <div id={"profile_courses"}>
        <ProductsSection
          productCardFlags={{ isOffer: true, isClient: true }}
          showSort={true}
          sectionTitle={"similarCourses"}
          pageSize={4}
        />
      </div>
    </>
  );
};

export default ProfilePage;
