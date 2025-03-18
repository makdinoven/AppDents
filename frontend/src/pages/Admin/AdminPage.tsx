import { Outlet } from "react-router-dom";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
import { useEffect } from "react";
import { getMe } from "../../store/actions/userActions.ts";

const AdminPage = () => {
  const dispatch = useDispatch<AppDispatchType>();

  useEffect(() => {
    dispatch(getMe());
  }, [dispatch]);

  return <Outlet />;
};

export default AdminPage;
