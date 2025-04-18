import { useDispatch, useSelector } from "react-redux";
import { logout } from "../../../../store/slices/userSlice.ts";
import { t } from "i18next";
import { useNavigate } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import BackButton from "../../../../components/ui/BackButton/BackButton.tsx";
import { useEffect, useState } from "react";
import { getCourses, getMe } from "../../../../store/actions/userActions.ts";
import { AppDispatchType, AppRootStateType } from "../../../../store/store.ts";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import LineWrapper from "../../../../components/ui/LineWrapper/LineWrapper.tsx";
import User from "../../../../assets/Icons/User.tsx";
import { Trans } from "react-i18next";
import MyCourses from "../../modules/MyCourses/MyCourses.tsx";
import ModalWrapper from "../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import ResetPasswordModal from "../../../../components/Modals/ResetPasswordModal.tsx";
// import ConfirmModal from "../../../../components/Modals/ConfirmModal/ConfirmModal.tsx";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  // const [showConfirmModal, setShowConfirmModal] = useState(false);
  const { loading, email } = useSelector(
    (state: AppRootStateType) => state.user,
  );

  const handleLogout = () => {
    navigate("/");
    dispatch(logout());
  };

  useEffect(() => {
    fetchData();
  }, [dispatch]);

  const fetchData = async () => {
    try {
      await dispatch(getMe());
      await dispatch(getCourses());
    } catch (error) {
      console.error(error);
    }
  };

  const handleModalClose = () => {
    setShowResetPasswordModal(false);
  };

  return (
    <>
      <BackButton />
      {loading ? (
        <Loader />
      ) : (
        <div className={s.profile_page}>
          <div className={s.page_header}>
            <div className={s.user_info}>
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
              </div>
            </div>
            <LineWrapper>
              <ArrowButton text={t("logout")} onClick={handleLogout} />
            </LineWrapper>
          </div>
          <MyCourses courses={courses} />
        </div>
      )}
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
