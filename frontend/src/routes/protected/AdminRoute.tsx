import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useNavigate } from "react-router-dom";
import { Path } from "../routes.ts";
import Loader from "../../components/ui/Loader/Loader.tsx";
import { useEffect } from "react";

const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const loading = useSelector((state: AppRootStateType) => state.user.loading);
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const isAdmin = role === "admin";

  useEffect(() => {
    if (!loading) {
      if (!isLogged) {
        navigate(Path.login, { replace: true, state: {} });
      } else if (!isAdmin) {
        navigate(Path.profile, { replace: true, state: {} });
      }
    }
  }, [loading, isLogged, isAdmin, navigate]);

  if (loading) {
    return <Loader />;
  }

  if (!isLogged || !isAdmin) {
    return null;
  }

  return <>{children}</>;
};

export default AdminRoute;
