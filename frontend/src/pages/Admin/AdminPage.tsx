import { Outlet } from "react-router-dom";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
import { useEffect } from "react";
import { getMe } from "../../store/actions/userActions.ts";
import i18n from "i18next";

const AdminPage = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const changeLanguage = (lang: string) => {
    i18n.changeLanguage(lang);
  };

  useEffect(() => {
    dispatch(getMe());
    changeLanguage("en");
  }, [dispatch]);

  return <Outlet />;
};

export default AdminPage;
