import "../../../components/ui/Button/Button.module.scss";
import s from "./CustomOrder.module.scss";
import { useForm } from "react-hook-form";
import { OrderDescriptionType } from "../../../api/userApi/types.ts";
import { Trans } from "react-i18next";
import Form from "../../Modals/modules/Form/Form.tsx";
import { t } from "i18next";
import Button from "../../ui/Button/Button.tsx";
import { useEffect, useState } from "react";
import { AlertCirceIcon, CheckMark, SendIcon } from "../../../assets/icons";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../store/store.ts";
import { userApi } from "../../../api/userApi/userApi.ts";
import { Alert } from "../../ui/Alert/Alert.tsx";
import { BRAND } from "../../../common/helpers/commonConstants.ts";
import { Caduceus, ToothGreen } from "../../../assets";
import { useLocation, useNavigate } from "react-router-dom";
import { Path } from "../../../routes/routes.ts";

const CustomOrder = () => {
  const {
    register,
    watch,
    handleSubmit,
    formState: { errors },
  } = useForm<OrderDescriptionType>({
    mode: "onSubmit",
  });
  const { id, language, isLogged } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const [loading, setLoading] = useState(false);
  const [isClickedWhileLoggedOut, setIsClickedWhileLoggedOut] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!isClickedWhileLoggedOut) return;

    const removeText = setTimeout(() => {
      setIsClickedWhileLoggedOut(false);
    }, 2000);

    return () => clearTimeout(removeText);
  }, [isClickedWhileLoggedOut]);

  const description = watch("description");

  const handleOrderSubmit = async () => {
    try {
      if (!id) return;
      setLoading(true);
      await userApi.requestProduct({ user_id: id, text: description });
      Alert(t("orderProduct.productRequestSuccess"), <CheckMark />);
    } catch {
      Alert(t("orderProduct.productRequestFailed"), <AlertCirceIcon />);
    } finally {
      setLoading(false);
    }
  };

  const handleLoggedOutButtonClick = () => {
    if (isLogged) return;

    setIsClickedWhileLoggedOut(true);
  };

  const handleOpenAuthModal = () => {
    navigate(Path.signUp, {
      state: { backgroundLocation: location },
    });
  };

  return (
    <div className={s.custom_order_block}>
      <h2>
        <Trans
          i18nKey={"orderProduct.customOrder"}
          components={[<span className={s.highlight} />]}
        />
      </h2>
      <div className={s.form}>
        <Form handleSubmit={handleSubmit(handleOrderSubmit)}>
          <div className={s.content_block}>
            <h3 lang={language.toLowerCase()}>
              <Trans i18nKey={"orderProduct.customOrderText"} />
            </h3>
            <div
              className={`${s.description_block} ${errors.description?.message ? s.error : ""}`}
            >
              <label htmlFor="description">
                <Trans
                  i18nKey={
                    errors.description?.message || "orderProduct.describeOrder"
                  }
                />
              </label>
              <textarea
                id="description"
                maxLength={1000}
                placeholder={t("orderProduct.typeHere")}
                {...register("description", {
                  required: t("error.description.required"),
                  minLength: {
                    value: 8,
                    message: t("error.description.minLength"),
                  },
                  maxLength: {
                    value: 999,
                    message: t("error.description.maxLength"),
                  },
                })}
              />
              {BRAND === "dents" ? (
                <ToothGreen />
              ) : (
                <Caduceus className={s[BRAND]} />
              )}
            </div>
          </div>
          <Button
            type={isLogged ? "submit" : "button"}
            disabled={loading}
            loading={loading}
            icon={<SendIcon />}
            variant="filled_dark"
            className={`${s.request_btn} ${!isLogged ? s.disabled : ""}`}
            onClick={() => handleLoggedOutButtonClick()}
          >
            <Trans i18nKey="orderProduct.request" />
          </Button>
          {!isLogged && (
            <p className={isClickedWhileLoggedOut ? s.highlight_red : ""}>
              <Trans
                i18nKey="orderProduct.loginText"
                components={[
                  <span
                    className={s.underline}
                    onClick={() => handleOpenAuthModal()}
                  />,
                ]}
              />
            </p>
          )}
        </Form>
      </div>
    </div>
  );
};
export default CustomOrder;
