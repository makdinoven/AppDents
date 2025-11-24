import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../shared/store/store.ts";
import { useNavigate } from "react-router-dom";
import { ReactNode, useEffect } from "react";
import Loader from "../../../shared/components/ui/Loader/Loader.tsx";
import { LS_TOKEN_KEY } from "../../../shared/common/helpers/commonConstants.ts";
import { PATHS } from "../routes.ts";

const ProtectedRoute = ({ children }: { children: ReactNode }) => {
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const loading = useSelector((state: AppRootStateType) => state.user.loading);
  const accessToken = localStorage.getItem(LS_TOKEN_KEY);

  useEffect(() => {
    if (!loading && !isLogged && !accessToken) {
      navigate(PATHS.LOGIN, { replace: true });
    }
  }, [loading, isLogged, navigate]);

  if (loading || (accessToken && !isLogged)) {
    return <Loader />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
