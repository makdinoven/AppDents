import s from "./ProfilePage.module.scss";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { useEffect } from "react";
import { getMe } from "../../store/actions/userActions.ts";
import { Outlet, useNavigate } from "react-router-dom";
import CoursesSection from "../MainPage/CoursesSection/CoursesSection.tsx";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import { Path } from "../../routes/routes.ts";
const ProfilePage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const { role } = useSelector((state: AppRootStateType) => state.user);
  const navigate = useNavigate();

  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

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
