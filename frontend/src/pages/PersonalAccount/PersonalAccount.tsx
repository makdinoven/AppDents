import Button from "../../components/ui/Button/Button.tsx";
import { useDispatch } from "react-redux";
import { logout } from "../../store/slices/userSlice.ts";
import { t } from "i18next";
import PrettyButton from "../../components/ui/PrettyButton/PrettyButton.tsx";
import { Path } from "../../routes/routes.ts";
import { useNavigate } from "react-router-dom";
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
    <>
      personal page
      <Button text={t("logout")} onClick={handleLogout} />
      <PrettyButton text={"admin"} onClick={() => navigate(Path.admin)} />
    </>
  );
};

export default PersonalAccountPage;
