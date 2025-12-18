import { useState } from "react";
import { useSelector } from "react-redux";
import { useForm } from "react-hook-form";
import { joiResolver } from "@hookform/resolvers/joi";
import { t } from "i18next";
import { AppRootStateType } from "@/shared/store/store";
import { changePasswordApi } from "../api/changePasswordApi";
import { ChangePasswordType } from "../model/types";
import { emailSchema } from "@/shared/common/schemas/emailSchema";
import { Alert } from "@/shared/components/ui/Alert/Alert";
import { CheckMark } from "@/shared/assets/icons";

type Props = {
  onSuccess?: () => void;
};

export const useForgotPasswordForm = ({ onSuccess }: Props = {}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChangePasswordType>({
    resolver: joiResolver(emailSchema),
    mode: "onTouched",
  });

  const onSubmit = async (data: ChangePasswordType) => {
    setLoading(true);
    setError(null);

    try {
      await changePasswordApi.forgotPassword({ email: data.email, language });
      Alert(t("forgotPasswordSuccess"), <CheckMark />);
      onSuccess?.();
    } catch (err: any) {
      setError(err.response?.data?.detail?.error?.translation_key || "error");
    } finally {
      setLoading(false);
    }
  };

  return {
    register,
    handleSubmit,
    errors,
    loading,
    error,
    onSubmit,
  };
};
