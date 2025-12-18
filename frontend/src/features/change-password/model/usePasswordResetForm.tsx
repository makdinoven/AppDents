import { useState } from "react";
import { useSelector } from "react-redux";
import { useForm } from "react-hook-form";
import { joiResolver } from "@hookform/resolvers/joi";
import { t } from "i18next";
import { AppRootStateType } from "@/shared/store/store";
import { ResetPasswordType } from "./types.ts";
import { resetPasswordSchema } from "@/shared/common/schemas/resetPasswordSchema";
import { Alert } from "@/shared/components/ui/Alert/Alert";
import { AlertCirceIcon, CheckMark } from "@/shared/assets/icons";
import { changePasswordApi } from "../api/changePasswordApi.ts";

export const usePasswordResetForm = () => {
  const { id, language } = useSelector((state: AppRootStateType) => state.user);
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordType>({
    resolver: joiResolver(resetPasswordSchema),
    mode: "onSubmit",
  });

  const onSubmit = async (data: ResetPasswordType) => {
    if (!id) return;

    try {
      setLoading(true);
      await changePasswordApi.resetPassword({ password: data.password, id });
      Alert(t("passwordChanged"), <CheckMark />); //TODO КОГДА БУДУТ ТОСТЫ ИСПОЛЬЗОВАТЬ ТОСТ
    } catch {
      Alert(t("error.errorChangingPassword"), <AlertCirceIcon />);
    } finally {
      setLoading(false);
    }
  };

  return {
    register,
    handleSubmit,
    errors,
    loading,
    onSubmit,
    language,
  };
};
