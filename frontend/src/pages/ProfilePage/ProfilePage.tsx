import s from "./ProfilePage.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { Outlet, useNavigate } from "react-router-dom";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import { Path } from "../../routes/routes.ts";
import ProductsSection from "../../components/ProductsSection/ProductsSection.tsx";

const ProfilePage = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const navigate = useNavigate();

  return (
    <>
      {role === "admin" && (
        <div className={s.admin_wrapper}>
          <PrettyButton
            variant="primary"
            text={"Admin panel"}
            onClick={() => navigate(Path.admin)}
          />
        </div>
      )}
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
