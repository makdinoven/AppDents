import { Outlet } from "react-router-dom";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import Loader from "../../components/ui/Loader/Loader.tsx";

const AdminPage = () => {
  const loading = useSelector((state: AppRootStateType) => state.user.loading);

  return <>{loading ? <Loader /> : <Outlet />}</>;
};

export default AdminPage;
