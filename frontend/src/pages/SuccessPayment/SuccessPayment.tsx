import { useNavigate, useSearchParams } from "react-router-dom";
import s from "./SuccessPayment.module.scss";
import { useEffect } from "react";
import { Trans } from "react-i18next";
import { useDispatch } from "react-redux";
import ReactPixel from "react-facebook-pixel";
import { AppDispatchType } from "../../shared/store/store.ts";
import { setLanguage } from "../../shared/store/slices/userSlice.ts";
import { PATHS } from "../../app/routes/routes.ts";
import { mainApi } from "../../shared/api/mainApi/mainApi.ts";
import {
  BRAND,
  LS_TOKEN_KEY,
} from "../../shared/common/helpers/commonConstants.ts";
import { getMe } from "../../shared/store/actions/userActions.ts";
import Loader from "../../shared/components/ui/Loader/Loader.tsx";
import {
  initAllMedgPixel,
  initFacebookPixel,
} from "../../shared/common/helpers/facebookPixel.ts";

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

    if (BRAND === "dents") {
      initFacebookPixel();
    } else {
      initAllMedgPixel();
      // if (
      //     landing.tags.some((tag: any) => tag.name === tag.plastic_surgery)
      // ) {
      //   initPlasticSurgeryMedgPixel();
      // }
    }

    if (sessionId) {
      getAndSetToken();
    } else {
      navigate(PATHS.MAIN);
    }
  }, [sessionId, region]);

  const getAndSetToken = async () => {
    try {
      const res = await mainApi.getTokenAfterPurchase({
        session_id: sessionId,
        region: region,
      });

      const { purchase_data } = res.data;

      if (purchase_data && purchase_data.amount > 0) {
        try {
          ReactPixel.trackCustom("Purchase", {
            value: purchase_data.amount,
            currency: purchase_data.currency,
            content_ids: purchase_data.content_ids,
            content_type: purchase_data.content_type,
            num_items: purchase_data.num_items,
            eventID: purchase_data.session_id,
          });
        } catch (pixelError) {
          console.error(
            "[Facebook Pixel] Failed to send Purchase event:",
            pixelError,
          );
        }
      } else {
        console.warn(
          "[Facebook Pixel] No purchase_data received or amount is 0",
        );
      }
      localStorage.setItem(LS_TOKEN_KEY, res.data.access_token);
      await dispatch(getMe());
      navigate(PATHS.PROFILE);
    } catch (error) {
      navigate(PATHS.MAIN);
      console.error("[SuccessPayment] Error:", error);
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
