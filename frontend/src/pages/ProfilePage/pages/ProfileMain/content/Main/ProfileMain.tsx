import { useDispatch, useSelector } from "react-redux";
import { useNavigate, useSearchParams } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import BackButton from "../../../../../../components/ui/BackButton/BackButton.tsx";
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
import MyCourses from "../../../../modules/MyCourses/MyCourses.tsx";
import ModalWrapper from "../../../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import ResetPasswordModal from "../../../../../../components/Modals/ResetPasswordModal.tsx";
import { Path } from "../../../../../../routes/routes.ts";
import {
  getCourses,
  logoutAsync,
} from "../../../../../../store/actions/userActions.ts";
import ReferralSection from "../../ReferralSection/ReferralSection.tsx";
import { clearCart } from "../../../../../../store/slices/cartSlice.ts";
import Tabs from "../../../../../../components/ui/Tabs/Tabs.tsx";
import PurchaseHistory from "../PurchaseHistory/PurchaseHistory.tsx";
import { useScreenWidth } from "../../../../../../common/hooks/useScreenWidth.ts";
import PrettyButton from "../../../../../../components/ui/PrettyButton/PrettyButton.tsx";

const QUERY_KEY = "content";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const email = useSelector((state: AppRootStateType) => state.user.email);
  const [searchParams] = useSearchParams();
  const tabFromParams = searchParams.get(QUERY_KEY);
  const screenWidth = useScreenWidth();

  useEffect(() => {
    if (!courses.length) dispatch(getCourses());
  }, []);

  const handleLogout = () => {
    dispatch(logoutAsync());
    dispatch(clearCart());
    setTimeout(() => {
      navigate(Path.main);
    }, 0);
  };

  const handleModalClose = () => {
    setShowResetPasswordModal(false);
  };

  const profilePageContent = [
    {
      name: "profile.main",
      value: "profile_main",
      component: (
        <>
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
          <MyCourses courses={courses} />
        </>
      ),
    },
    {
      name: "profile.yourCourses",
      value: "your_courses",
      component: <MyCourses courses={courses} />,
    },
    {
      name: "profile.purchaseHistory.purchases",
      value: "purchase_history",
      component: <PurchaseHistory />,
    },
  ];

  const activeTab =
    profilePageContent.find((tab) => tab.value === tabFromParams) ??
    profilePageContent.find((tab) => tab.value === "profile_main");

  return (
    <>
      <div className={s.back_btn_tabs_container}>
        {screenWidth > 576 && <BackButton />}

        <Tabs
          queryKey={QUERY_KEY}
          mainTab={"profile_main"}
          tabs={profilePageContent}
        />
      </div>

      <div className={s.profile_page_content}>{activeTab?.component}</div>

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
