import { getAuthHeaders, instance } from "@/shared/api";
import { ChangePasswordDTO, ResetPasswordDTO } from "../model/types.ts";

export const changePasswordApi = {
  forgotPassword({ email, language }: ChangePasswordDTO) {
    return instance.post(
      `users/forgot-password`,
      { email },
      {
        params: {
          region: language,
        },
      },
    );
  },

  resetPassword({ password, id }: ResetPasswordDTO) {
    return instance.put(`users/${id}/password`, password, {
      headers: getAuthHeaders(),
    });
  },
};
