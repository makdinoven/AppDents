import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import ModalLink from "./modules/ModalLink.tsx";
import Form from "./modules/Form.tsx";
import Input from "./modules/Input.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import { useForm } from "../../common/hooks/useForm.ts";
import { emailSchema } from "../../common/schemas/emailSchema.ts";
import { Path } from "../../routes/routes.ts";

const ResetPasswordModal = () => {
  const { values, errors, handleChange, handleSubmit } = useForm({
    validationSchema: emailSchema,
    onSubmit: (data) => console.log("reset pass data:", data),
  });

  return (
    <div className={s.modal}>
      <h3>
        <Trans i18nKey={"passwordReset"} />
      </h3>
      <Form handleSubmit={handleSubmit}>
        <>
          <Input
            name="email"
            id="emailResetPassword"
            placeholder={t("email")}
            value={values.email || ""}
            onChange={handleChange}
            error={errors?.email}
          />
          <Button text={t("reset")} type="submit" />
        </>
      </Form>
      <div className={s.modal_bottom}>
        <span>
          <Trans i18nKey={"passwordResetMailSent"} />
        </span>
        <ModalLink link={Path.login} text={"backToLogin"} />
      </div>
    </div>
  );
};

export default ResetPasswordModal;
