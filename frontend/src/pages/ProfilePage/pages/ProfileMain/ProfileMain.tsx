import { useDispatch, useSelector } from "react-redux";
import { useLocation, useNavigate } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import { useEffect } from "react";
import { AppDispatchType, AppRootStateType } from "@/shared/store/store.ts";
import {
  LogoutIcon,
  Mail,
  Support,
  User,
} from "../../../../shared/assets/icons";
import { Trans } from "react-i18next";
import {
  getBooks,
  getCourses,
  logoutAsync,
} from "@/shared/store/actions/userActions.ts";
import { clearCart } from "@/shared/store/slices/cartSlice.ts";
import { logout } from "@/shared/store/slices/userSlice.ts";
import ReferralSection from "./modules/ReferralSection/ReferralSection.tsx";
import MyContent from "../modules/MyContent/MyContent.tsx";
import { PATHS } from "@/app/routes/routes.ts";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const books = useSelector((state: AppRootStateType) => state.user.books);
  const email = useSelector((state: AppRootStateType) => state.user.email);
  const location = useLocation();
  const childKey = location.pathname.slice(1);

  useEffect(() => {
    if (!courses.length) dispatch(getCourses());
    if (!books.length) dispatch(getBooks());
  }, []);

  const handleLogout = async () => {
    await dispatch(logoutAsync());
    dispatch(clearCart());
    dispatch(logout());
    setTimeout(() => {
      navigate(PATHS.MAIN);
    }, 0);
  };

  return (
    <div className={s.page_content}>
      <div key={childKey} className={s.main_content}>
        <div className={s.main_content_top}>
          <div className={s.profile}>
            <div className={s.profile_header}>
              <p className={s.section_title}>
                <Trans i18nKey="profile.profile" />
              </p>
              <button className={s.logout} onClick={() => handleLogout()}>
                <LogoutIcon />
                <Trans i18nKey="logout" />
              </button>
            </div>
            <div className={s.profile_content}>
              <User className={s.user} />
              <div className={s.profile_info}>
                <div className={s.mail}>
                  <Mail />
                  <span>
                    <Trans i18nKey="mail" />:
                  </span>
                  {email}
                </div>
                <div className={s.support}>
                  <Support />
                  <span>
                    <Trans i18nKey="support" />:
                  </span>{" "}
                  <a
                    className={s.mail_link}
                    href="mailto:info.dis.org@gmail.com"
                  >
                    info.dis.org@gmail.com
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        <ReferralSection />
      </div>
      <MyContent key="books" items={books} type="book" />
      <MyContent key="courses" items={courses} />
    </div>
  );
};

export default ProfileMain;
