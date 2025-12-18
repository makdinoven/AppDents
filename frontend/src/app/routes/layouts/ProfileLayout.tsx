import s from "../../../pages/ProfilePage/layout/ProfilePage.module.scss";
import { Outlet } from "react-router-dom";
import ProductsSection from "../../../shared/components/ProductsSection/ProductsSection.tsx";
import CustomOrder from "../../../shared/components/CustomOrder/CustomOrder.tsx";

const ProfileLayout = () => {
  return (
    <>
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
