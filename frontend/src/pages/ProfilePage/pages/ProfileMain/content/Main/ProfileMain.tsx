import { useDispatch, useSelector } from "react-redux";
import { useLocation, useNavigate } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import { useEffect, useState } from "react";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../../../store/store.ts";
import {
  LogoutIcon,
  Mail,
  Support,
  User,
} from "../../../../../../assets/icons";
import { Trans } from "react-i18next";
import ModalWrapper from "../../../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import ResetPasswordModal from "../../../../../../components/Modals/ResetPasswordModal.tsx";
import { Path } from "../../../../../../routes/routes.ts";
import {
  getBooks,
  getCourses,
  logoutAsync,
} from "../../../../../../store/actions/userActions.ts";
import ReferralSection from "../../ReferralSection/ReferralSection.tsx";
import { clearCart } from "../../../../../../store/slices/cartSlice.ts";
import PrettyButton from "../../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import MyContent from "../../../modules/MyContent/MyContent.tsx";
import { logout } from "../../../../../../store/slices/userSlice.ts";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const books = useSelector((state: AppRootStateType) => state.user.books);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
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
      navigate(Path.main);
    }, 0);
  };

  const handleModalClose = () => {
    setShowResetPasswordModal(false);
  };

  return (
    <>
      <div key={childKey} className={s.profile_page_content}>
        <div className={s.page_header}>
          <div className={s.user_info}>
            <div className={s.left}>
              <div className={s.user_top}>
                <User className={s.user_icon} />
                <div className={s.user_items}>
                  <div>
                    <div className={s.mail}>
                      <Mail />
                      <Trans i18nKey="mail" />:{" "}
                    </div>
                    {email}
                  </div>
                  <div>
                    <div className={s.support}>
                      <Support />
                      <Trans i18nKey="support" />:{" "}
                    </div>
                    <a
                      className={s.mail_link}
                      href="mailto:info.dis.org@gmail.com"
                    >
                      info.dis.org@gmail.com
                    </a>
                  </div>
                </div>
              </div>
              <div className={s.profile_buttons}>
                <button onClick={handleLogout} className={s.logout_btn}>
                  <LogoutIcon />
                  <Trans i18nKey="logout" />
                </button>
                <PrettyButton
                  className={s.reset_pass_btn}
                  variant="danger"
                  onClick={() => setShowResetPasswordModal(true)}
                  text={"resetPassword"}
                />
              </div>
            </div>
            <ReferralSection />
          </div>
        </div>
        <MyContent key="books" items={books} type="book" />
        <MyContent key="courses" items={courses} />
      </div>

      {showResetPasswordModal && (
        <ModalWrapper
          title={"resetPassword"}
          cutoutPosition={"none"}
          isOpen={showResetPasswordModal}
          onClose={handleModalClose}
        >
          <ResetPasswordModal handleClose={handleModalClose} />
        </ModalWrapper>
      )}
    </>
  );
};

export default ProfileMain;
