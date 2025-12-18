import s from "./LogOutBtn.module.scss";
import { LogoutIcon } from "@/shared/assets/icons";
import { Trans } from "react-i18next";
import { logoutAsync } from "@/shared/store/actions/userActions.ts";
import { clearCart } from "@/shared/store/slices/cartSlice.ts";
import { logout } from "@/shared/store/slices/userSlice.ts";
import { PATHS } from "@/app/routes/routes.ts";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "@/shared/store/store.ts";
import { useNavigate } from "react-router-dom";

export const LogOutBtn = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await dispatch(logoutAsync());
    dispatch(clearCart());
    dispatch(logout());
    setTimeout(() => {
      navigate(PATHS.MAIN);
    }, 0);
  };

  return (
    <button className={s.logout} onClick={() => handleLogout()}>
      <LogoutIcon />
      <Trans i18nKey="logout" />
    </button>
  );
};
