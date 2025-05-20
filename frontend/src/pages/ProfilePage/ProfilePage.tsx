import s from "./ProfilePage.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { Outlet, useNavigate } from "react-router-dom";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import { Path } from "../../routes/routes.ts";
import CoursesSection from "../../components/CommonComponents/CoursesSection/CoursesSection.tsx";
import Loader from "../../components/ui/Loader/Loader.tsx";

const ProfilePage = () => {
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const loading = useSelector((state: AppRootStateType) => state.user.loading);
  const navigate = useNavigate();

  if (loading) return <Loader />;

  return (
    <>
      <div className={s.admin_wrapper}>
        {role === "admin" && (
          <PrettyButton
            variant="primary"
            text={"Admin panel"}
            onClick={() => navigate(Path.admin)}
          />
        )}
      </div>
      <div className={s.profilePage}>
        <Outlet />
      </div>
      <CoursesSection
        showSort={true}
        sectionTitle={"similarCourses"}
        pageSize={4}
      />
    </>
  );
};

export default ProfilePage;
