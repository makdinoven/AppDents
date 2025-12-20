import s from "./Layout.module.scss";
import { Outlet } from "react-router-dom";
import ProductsSection from "../../../shared/components/ProductsSection/ProductsSection.tsx";
import CustomOrder from "../../../shared/components/CustomOrder/CustomOrder.tsx";

const ProfileLayout = () => {
  return (
    <div className={s.profile_page_wrapper}>
      <Outlet />
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
  );
};

export default ProfileLayout;
