import s from "./ProfilePage.module.scss";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
import { useEffect } from "react";
import { getMe } from "../../store/actions/userActions.ts";
import { Outlet } from "react-router-dom";
import CoursesSection from "../MainPage/CoursesSection/CoursesSection.tsx";
const PAGE_SIZE = 4;

const ProfilePage = () => {
  const dispatch = useDispatch<AppDispatchType>();

  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

  return (
    <>
      <div className={s.profilePage}>
        <Outlet />
      </div>
      <CoursesSection sectionTitle={"similarCourses"} pageSize={PAGE_SIZE} />
    </>
  );
};

export default ProfilePage;
