import { useDispatch, useSelector } from "react-redux";
import { logout } from "../../../../store/slices/userSlice.ts";
import { t } from "i18next";
import { Path } from "../../../../routes/routes.ts";
import { useNavigate } from "react-router-dom";
import s from "./ProfileMain.module.scss";
import BackButton from "../../../../components/ui/BackButton/BackButton.tsx";
import { useEffect } from "react";
import { getCourses, getMe } from "../../../../store/actions/userActions.ts";
import { AppDispatchType } from "../../../../store/store.ts";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import { AppRootStateType } from "../../../../store/store.ts";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import LineWrapper from "../../../../components/ui/LineWrapper/LineWrapper.tsx";
import User from "../../../../assets/Icons/User.tsx";
import { Trans } from "react-i18next";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";
import MyCourses from "../../modules/MyCourses/MyCourses.tsx";

const ProfileMain = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const courses = useSelector((state: AppRootStateType) => state.user.courses);
  const { role, loading, email } = useSelector(
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

      <BackButton />
      {loading ? (
        <Loader />
      ) : (
        <div className={s.profile_page}>
          <div className={s.page_header}>
            <div className={s.user_info}>
              <User />
              <div>
                <span>
                  <Trans i18nKey="mail" />:{" "}
                </span>
                {email}
              </div>
            </div>
            <LineWrapper>
              <ArrowButton text={t("logout")} onClick={handleLogout} />
            </LineWrapper>
          </div>
          <MyCourses courses={courses} />
        </div>
      )}
    </>
  );
};

export default ProfileMain;
