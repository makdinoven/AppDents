import s from "../../../pages/ProfilePage/layout/ProfilePage.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../shared/store/store.ts";
import { Outlet, useNavigate } from "react-router-dom";
import PrettyButton from "../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import ProductsSection from "../../../shared/components/ProductsSection/ProductsSection.tsx";
import CustomOrder from "../../../shared/components/CustomOrder/CustomOrder.tsx";
import { PATHS } from "../routes.ts";

const ProfileLayout = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const navigate = useNavigate();

  return (
    <>
      {role === "admin" && (
        <div className={s.admin_wrapper}>
          <PrettyButton
            variant="primary"
            text={"Admin panel"}
            onClick={() => navigate(PATHS.ADMIN_LANDINGS_LISTING)}
          />
        </div>
      )}
      <Outlet />
      <div className={s.profile_page_wrapper}>
        <div id={"profile_courses"}>
          <ProductsSection
            productCardFlags={{ isOffer: true, isClient: true }}
            showSort={true}
            sectionTitle={"similarCourses"}
            pageSize={4}
          />
        </div>
        <CustomOrder />
      </div>
    </>
  );
};

export default ProfileLayout;
