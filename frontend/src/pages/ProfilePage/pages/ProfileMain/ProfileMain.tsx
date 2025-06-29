import { useDispatch, useSelector } from "react-redux";
import { t } from "i18next";
import { useNavigate } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import BackButton from "../../../../components/ui/BackButton/BackButton.tsx";
import { useEffect, useState } from "react";
import { AppDispatchType, AppRootStateType } from "../../../../store/store.ts";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import LineWrapper from "../../../../components/ui/LineWrapper/LineWrapper.tsx";
import User from "../../../../assets/icons/User.tsx";
import { Trans } from "react-i18next";
import MyCourses from "../../modules/MyCourses/MyCourses.tsx";
import ModalWrapper from "../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import ResetPasswordModal from "../../../../components/Modals/ResetPasswordModal.tsx";
import { Path } from "../../../../routes/routes.ts";
import {
  getCourses,
  logoutAsync,
} from "../../../../store/actions/userActions.ts";
import ReferralSection from "./ReferralSection/ReferralSection.tsx";
import { clearCart } from "../../../../store/slices/cartSlice.ts";
// import ConfirmModal from "../../../../components/Modals/ConfirmModal/ConfirmModal.tsx";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  // const [showConfirmModal, setShowConfirmModal] = useState(false);
  const email = useSelector((state: AppRootStateType) => state.user.email);
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged
  );

  const handleLogout = () => {
    dispatch(logoutAsync());
    dispatch(clearCart());
    setTimeout(() => {
      navigate(Path.main);
    }, 0);
  };

  useEffect(() => {
    if (isLogged) {
      dispatch(getCourses());
    }
  }, [dispatch]);

  const handleModalClose = () => {
    setShowResetPasswordModal(false);
  };

  return (
    <>
      <BackButton />
      <div className={s.profile_page}>
        <div className={s.page_header}>
          <div className={s.user_info}>
            <div className={s.left}>
              <User />
              <div className={s.user_items}>
                <div>
                  <span>
                    <Trans i18nKey="mail" />:{" "}
                  </span>
                  {email}
                </div>
                <PrettyButton
                  variant="danger"
                  onClick={() => setShowResetPasswordModal(true)}
                  text={"resetPassword"}
                />
                <div>
                  <span>
                    <Trans i18nKey="support" />:{" "}
                  </span>
                  <a
                    className={s.mail_link}
                    href="mailto:info.dis.org@gmail.com"
                  >
                    info.dis.org@gmail.com
                  </a>
                </div>
              </div>
            </div>
            <ReferralSection />
          </div>

          <LineWrapper>
            <ArrowButton text={t("logout")} onClick={handleLogout} />
          </LineWrapper>
        </div>
        <MyCourses courses={courses} />
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

      {/*{showConfirmModal && <ConfirmModal />}*/}
    </>
  );
};

export default ProfileMain;
