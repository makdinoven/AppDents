import { useDispatch } from "react-redux";
import { logout } from "../../store/slices/userSlice.ts";
import { t } from "i18next";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import { Path } from "../../routes/routes.ts";
import { useNavigate } from "react-router-dom";
import s from "./PersonalAccount.module.scss";
import BackButton from "../../components/ui/BackButton/BackButton.tsx";
import { useEffect } from "react";
import { getMe } from "../../store/actions/userActions.ts";
import { AppDispatchType } from "../../store/store.ts";
// import { AppRootStateType } from "../../store/store.ts";

const PersonalAccountPage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  // const role = useSelector((state: AppRootStateType) => state.user.role);
  const navigate = useNavigate();

  const handleLogout = () => {
    dispatch(logout());
  };

  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

  // useEffect(() => {
  //   if (!role) {
  //     navigate(Path.login);
  //   }
  // }, [role]);

  return (
    <>
      <BackButton />
      <div className={s.profile_page}>
        <PrettyButton text={"admin"} onClick={() => navigate(Path.admin)} />
        <PrettyButton
          variant={"danger"}
          text={t("logout")}
          onClick={handleLogout}
        />
      </div>
    </>
  );
};

export default PersonalAccountPage;
