import { useDispatch, useSelector } from "react-redux";
import { useLocation } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import { useEffect } from "react";
import { AppDispatchType, AppRootStateType } from "@/shared/store/store.ts";
import { getBooks, getCourses } from "@/shared/store/actions/userActions.ts";
import ReferralSection from "./modules/ReferralSection/ReferralSection.tsx";
import MyContent from "../modules/MyContent/MyContent.tsx";
import { t } from "i18next";
import { NavigateToSupport } from "@/features/navigate-to-support";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const books = useSelector((state: AppRootStateType) => state.user.books);
  const location = useLocation();
  const childKey = location.pathname.slice(1);

  useEffect(() => {
    if (!courses.length) dispatch(getCourses());
    if (!books.length) dispatch(getBooks());
  }, []);

  return (
    <div className={s.page_content}>
      <div key={childKey} className={s.main_content}>
        <p className={s.page_title}>{t("profile.main")}</p>
        <ReferralSection />
        <NavigateToSupport />
      </div>
      <MyContent key="books" items={books} type="book" />
      <MyContent key="courses" items={courses} />
    </div>
  );
};

export default ProfileMain;
