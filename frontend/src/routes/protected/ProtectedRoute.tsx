import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useNavigate } from "react-router-dom";
import { Path } from "../routes.ts";
import { useEffect } from "react";
import Loader from "../../components/ui/Loader/Loader.tsx";
import { LS_TOKEN_KEY } from "../../common/helpers/commonConstants.ts";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const loading = useSelector((state: AppRootStateType) => state.user.loading);
  const accessToken = localStorage.getItem(LS_TOKEN_KEY);

  useEffect(() => {
    if (!loading && !isLogged && !accessToken) {
      navigate(Path.login, { replace: true });
    }
  }, [loading, isLogged, navigate]);

  if (loading || (accessToken && !isLogged)) {
    return <Loader />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
