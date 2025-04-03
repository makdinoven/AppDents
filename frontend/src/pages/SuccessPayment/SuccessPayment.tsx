import { useNavigate, useSearchParams } from "react-router-dom";
import s from "./SuccessPayment.module.scss";
import { useEffect } from "react";
import Loader from "../../components/ui/Loader/Loader.tsx";
import { Trans } from "react-i18next";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { getMe } from "../../store/actions/userActions.ts";
import { useDispatch } from "react-redux";
import { AppDispatchType } from "../../store/store.ts";
import { Path } from "../../routes/routes.ts";
import { setLanguage } from "../../store/slices/userSlice.ts";

const SuccessPayment = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const region = searchParams.get("region");

  useEffect(() => {
    if (region) {
      dispatch(setLanguage(region));
    }
    if (sessionId) {
      getAndSetToken();
    }
  }, [sessionId, region]);

  const getAndSetToken = async () => {
    try {
      console.log(sessionId);
      console.log(region);
      const res = await mainApi.getTokenAfterPurchase({
        session_id: sessionId,
        region: region,
      });
      localStorage.setItem("access_token", res.data.access_token);
      await dispatch(getMe());
      navigate(Path.profile);
    } catch (error) {
      navigate(Path.main);
      console.error(error);
    }
  };

  return (
    <div className={s.successPayment}>
      <Loader />
      <p className={s.text}>
        <Trans i18nKey="successPayment" />
      </p>
    </div>
  );
};

export default SuccessPayment;
