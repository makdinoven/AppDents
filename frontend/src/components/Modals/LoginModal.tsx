import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import { t } from "i18next";
import { loginSchema } from "../../common/schemas/loginSchema.ts";
import Form from "./modules/Form/Form.tsx";
import Input from "./modules/Input/Input.tsx";
import Button from "../ui/Button/Button.tsx";
import ModalLink from "./modules/ModalLink/ModalLink.tsx";
import { Path } from "../../routes/routes.ts";
import { getMe, login } from "../../store/actions/userActions.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../store/store.ts";
import { LoginType } from "../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";

const LoginModal = ({ onClose }: { onClose: () => void }) => {
  const dispatch = useDispatch<AppDispatchType>();
  const { error } = useSelector((state: AppRootStateType) => state.user);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginType>({
    resolver: joiResolver(loginSchema),
    mode: "onTouched",
  });

  const handleLogIn = async (data: LoginType) => {
    const loginResponse = await dispatch(login(data));

    if (loginResponse.meta.requestStatus === "fulfilled") {
      await dispatch(getMe());
      onClose();
    } else {
      console.log(loginResponse.payload);
    }
  };

  return (
    <div className={s.modal}>
      <Form handleSubmit={handleSubmit(handleLogIn)}>
        <>
          <Input
            type="email"
            id="email"
            placeholder={t("email")}
            {...register("email")}
            error={errors.email?.message}
          />

          <Input
            type="password"
            id="password"
            placeholder={t("password")}
            {...register("password")}
            error={errors.password?.message}
          />
          <Button text={t("login")} type="submit" />
        </>
      </Form>
      <div className={s.modal_bottom}>
        {error?.detail?.error?.translation_key && (
          <p className={s.error_message}>
            <Trans i18nKey={error.detail.error.translation_key} />
          </p>
        )}
        <span>
          <Trans i18nKey={"firstTimeHere"} />
          <ModalLink variant={"uppercase"} link={Path.signUp} text={"signup"} />
        </span>
        <ModalLink link={Path.passwordReset} text={"forgotPassword"} />
      </div>
    </div>
  );
};

export default LoginModal;
