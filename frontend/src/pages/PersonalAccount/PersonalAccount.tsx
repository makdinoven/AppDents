import { useDispatch } from "react-redux";
import { logout } from "../../store/slices/userSlice.ts";
import { t } from "i18next";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import { Path } from "../../routes/routes.ts";
import { useNavigate } from "react-router-dom";
import s from "./PersonalAccount.module.scss";
// import { AppRootStateType } from "../../store/store.ts";
// import { useEffect } from "react";

const PersonalAccountPage = () => {
  const dispatch = useDispatch();
  // const role = useSelector((state: AppRootStateType) => state.user.role);
  const navigate = useNavigate();

  const handleLogout = () => {
    dispatch(logout());
  };

  // useEffect(() => {
  //   if (!role) {
  //     navigate(Path.login);
  //   }
  // }, [role]);

  return (
    <div className={s.profile_page}>
      <PrettyButton text={"admin"} onClick={() => navigate(Path.admin)} />
      <PrettyButton
        variant={"danger"}
        text={t("logout")}
        onClick={handleLogout}
      />
    </div>
  );
};

export default PersonalAccountPage;
