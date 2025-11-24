import s from "./FriendMailInput.module.scss";
import { Trans } from "react-i18next";
import Form from "../../../../../../shared/components/Modals/modules/Form/Form.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../../shared/store/store.ts";
import { EnterEmailType } from "../../../../../../shared/api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { useForm } from "react-hook-form";
import { AlertCirceIcon, CheckMark } from "../../../../../../shared/assets/icons";
import { Ref, useEffect, useState } from "react";
import EmailInput from "../../../../../../shared/components/ui/Inputs/EmailInput/EmailInput.tsx";
import { emailSchema } from "../../../../../../shared/common/schemas/emailSchema.ts";
import Button from "../../../../../../shared/components/ui/Button/Button.tsx";
import ModalCloseButton from "../../../../../../shared/components/ui/ModalCloseButton/ModalCloseButton.tsx";
import { t } from "i18next";
import { userApi } from "../../../../../../shared/api/userApi/userApi.ts";
import { Alert } from "../../../../../../shared/components/ui/Alert/Alert.tsx";

interface FriendMailInputProps {
  closeModal: () => void;
  ref: Ref<HTMLDivElement>;
}

const FriendMailInput = ({ closeModal, ref }: FriendMailInputProps) => {
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
  } = useForm<EnterEmailType>({
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
      Alert(t("profile.referrals.inviteSuccess"), <CheckMark />);
    } catch {
      Alert(t("profile.referrals.inviteFailed"), <AlertCirceIcon />);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.modal} ref={ref}>
      <ModalCloseButton
        className={s.close_button}
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
        <Button
          text="profile.referrals.sendInvite"
          type="submit"
          variant="filled"
          loading={loading}
          disabled={loading}
          className={s.submit_btn}
        />
      </Form>
    </div>
  );
};

export default FriendMailInput;
