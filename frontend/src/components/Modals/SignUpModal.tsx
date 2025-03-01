import s from "./CommonModalStyles.module.scss";
import { Trans } from "react-i18next";
import ModalLink from "./modules/ModalLink.tsx";
import Input from "./modules/Input.tsx";
import { t } from "i18next";
import Button from "../ui/Button/Button.tsx";
import Form from "./modules/Form.tsx";
import { useForm } from "../../common/hooks/useForm.ts";
import { emailSchema } from "../../common/schemas/emailSchema.ts";
import { Path } from "../../routes/routes.ts";

const SignUpModal = () => {
  const { values, errors, handleChange, handleSubmit } = useForm({
    validationSchema: emailSchema,
    onSubmit: (data) => console.log(data),
  });

  return (
    <div className={s.modal}>
      <h3>
        <Trans i18nKey={"signup"} />
      </h3>
      <Form handleSubmit={handleSubmit}>
        <>
          <Input
            id="emailSignUp"
            name="email"
            value={values.email || ""}
            placeholder={t("email")}
            onChange={handleChange}
            error={errors?.email}
          />
          <Button text={t("signup")} type="submit" />
        </>
      </Form>
      <div className={s.modal_bottom}>
        <span>
          <Trans i18nKey={"alreadyHaveAccount"} />
        </span>
        <ModalLink link={Path.login} text={"login"} />
      </div>
    </div>
  );
};

export default SignUpModal;
