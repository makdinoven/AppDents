import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../shared/store/store.ts";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { PATHS } from "../routes.ts";

const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate();
  const role = useSelector((state: AppRootStateType) => state.user.role);
  const isAdmin = role === "admin";

  useEffect(() => {
    if (!isAdmin) {
      navigate(PATHS.PROFILE, { replace: true, state: {} });
    }
  }, [isAdmin, navigate]);

  if (!isAdmin) {
    return null;
  }

  return <>{children}</>;
};

export default AdminRoute;
