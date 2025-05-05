import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { useNavigate } from "react-router-dom";
import { Path } from "../routes.ts";
import Loader from "../../components/ui/Loader/Loader.tsx";
import { useEffect } from "react";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate();
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const loading = useSelector((state: AppRootStateType) => state.user.loading);

  useEffect(() => {
    if (!loading && !isLogged) {
      console.log("dddd");
      navigate(Path.login, { replace: true });
    }
  }, [loading, isLogged, navigate]);

  if (loading) {
    return <Loader />;
  }

  if (!isLogged) {
    return null;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
