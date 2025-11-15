import s from "./FriendMailInput.module.scss";
import { Trans } from "react-i18next";
import Form from "../../../../../../../../components/Modals/modules/Form/Form.tsx";
// import { t } from "i18next";
// import { userApi } from "../../../../../../../../api/userApi/userApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../../../../store/store.ts";
import { ChangePasswordType } from "../../../../../../../../api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
// import { Alert } from "../../../../../../../../components/ui/Alert/Alert.tsx";
// import {
//   AlertCirceIcon,
//   CheckMark,
// } from "../../../../../../../../assets/icons";
import { useEffect, useState } from "react";
import EmailInput from "../../../../../../../../components/ui/Inputs/EmailInput/EmailInput.tsx";
import { emailSchema } from "../../../../../../../../common/schemas/emailSchema.ts";
import Button from "../../../../../../../../components/ui/Button/Button.tsx";
import ModalCloseButton from "../../../../../../../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import { t } from "i18next";
import { userApi } from "../../../../../../../../api/userApi/userApi.ts";

interface FriendMailInputProps {
  closeModal: () => void;
}

const FriendMailInput = ({ closeModal }: FriendMailInputProps) => {
  const { language } = useSelector((state: AppRootStateType) => state.user);
  const [loading, setLoading] = useState<boolean>(false);
  const [email, setEmail] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    trigger,
    setFocus,
    formState: { errors },
  } = useForm<ChangePasswordType>({
    resolver: joiResolver(emailSchema),
    mode: "onTouched",
  });

  const emailValue = watch("email");

  useEffect(() => {
    if (emailValue) setEmail(emailValue);
  }, [emailValue]);

  useEffect(() => {
    if (!emailValue) return;

    const validateEmail = async () => {
      const ok = await trigger("email");

      if (!ok) {
        setFocus("email");
      }
    };

    validateEmail();
  }, [emailValue, trigger, setFocus]);

  const handleInviteFriend = async () => {
    try {
      setLoading(true);
      await userApi.inviteFriend({ recipient_email: email, language });
    } catch {
      setLoading(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.modal}>
      <ModalCloseButton
        className={s.close_modal_button}
        onClick={() => closeModal()}
      />
      <Form handleSubmit={handleSubmit(handleInviteFriend)}>
        <h3>
          <Trans i18nKey="profile.referrals.enterFriendsMail" />
        </h3>
        <div className={s.email_input_field}>
          <label htmlFor="email">
            <Trans i18nKey="profile.referrals.inviteFriendLabel" />
          </label>
          <EmailInput
            id="email"
            error={errors.email?.message}
            placeholder={t("email")}
            {...register("email")}
            isValidationUsed
            value={emailValue}
            setValue={setValue}
            {...{ variant: "invite" }}
          />
        </div>
        <div className={s.submit_button}>
          <Button
            text="profile.referrals.sendInvite"
            type="submit"
            variant="filled"
            loading={loading}
            disabled={loading}
            onClick={() => {}}
          />
        </div>
      </Form>
    </div>
  );
};

export default FriendMailInput;
