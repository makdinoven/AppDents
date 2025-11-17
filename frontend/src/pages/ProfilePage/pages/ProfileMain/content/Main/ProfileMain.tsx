import { useDispatch, useSelector } from "react-redux";
import { useLocation, useNavigate } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import { useEffect, useRef, useState } from "react";
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
import PasswordReset from "./modules/PasswordReset/PasswordReset.tsx";
import { Path } from "../../../../../../routes/routes.ts";
import {
  getBooks,
  getCourses,
  logoutAsync,
} from "../../../../../../store/actions/userActions.ts";
import { clearCart } from "../../../../../../store/slices/cartSlice.ts";
import { logout } from "../../../../../../store/slices/userSlice.ts";
import ReferralSection from "../../ReferralSection/ReferralSection.tsx";
import FriendMailInput from "./modules/FriendMailInput/FriendMailInput.tsx";
import ModalOverlay from "../../../../../../components/Modals/ModalOverlay/ModalOverlay.tsx";
import useOutsideClick from "../../../../../../common/hooks/useOutsideClick.ts";
import MyContent from "../../../modules/MyContent/MyContent.tsx";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const books = useSelector((state: AppRootStateType) => state.user.books);
  const [showInviteFriendModal, setShowInviteFriendModal] = useState(false);
  const email = useSelector((state: AppRootStateType) => state.user.email);
  const location = useLocation();
  const childKey = location.pathname.slice(1);
  const closeModalRef = useRef<() => void>(null);
  const modalRef = useRef<HTMLDivElement>(null);

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
    setShowInviteFriendModal(false);
  };

  useOutsideClick(modalRef, () => {
    handleModalClose();
    closeModalRef.current?.();
  });

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
          <div className={s.settings}>
            <p className={s.section_title}>
              <Trans i18nKey="profile.settings" />
            </p>

            <PasswordReset />
          </div>
        </div>
        <ReferralSection
          openInviteFriendModal={() => setShowInviteFriendModal(true)}
        />
      </div>
      <MyContent key="books" items={books} type="book" />
      <MyContent key="courses" items={courses} />

      <ModalOverlay
        isVisibleCondition={showInviteFriendModal}
        modalPosition="top"
        customHandleClose={handleModalClose}
        onInitClose={(fn) => (closeModalRef.current = fn)}
      >
        <FriendMailInput closeModal={handleModalClose} ref={modalRef} />
      </ModalOverlay>
    </div>
  );
};

export default ProfileMain;
