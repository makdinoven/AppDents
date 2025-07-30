import { useEffect, useState } from "react";
import useDebounce from "./useDebounce.ts";
import { userApi } from "../../api/userApi/userApi.ts";
import { ConfirmedEmail, ProcessEmail, WarningEmail } from "../../assets/icons";
import { emailSchema } from "../schemas/emailSchema.ts";

const State = {
  idle: { name: "idle", icon: null, msg: null },
  success: { name: "success", icon: <ConfirmedEmail />, msg: null },
  validating: { name: "validating", icon: <ProcessEmail />, msg: null },
  suggestion: {
    name: "suggestion",
    icon: <WarningEmail />,
    msg: "emailValidationTooltip.suggestion",
  },
  warning: {
    name: "warning",
    icon: <WarningEmail />,
    msg: "emailValidationTooltip.warning",
  },
} as const;

interface useEmailValidationResult {
  state: (typeof State)[keyof typeof State];
  suggestedEmail?: string;
}

export const useEmailValidation = (
  email?: string,
  formError?: boolean,
): useEmailValidationResult => {
  const [result, setResult] = useState<useEmailValidationResult>({
    state: State.idle,
  });
  const debouncedEmail = useDebounce(email, 300);

  // console.log(formError);

  useEffect(() => {
    const isEmailInvalid =
      !debouncedEmail ||
      !!emailSchema.validate({ email: debouncedEmail }).error ||
      formError;

    if (!isEmailInvalid) {
      handleEmailCheck(debouncedEmail);
    } else {
      setResult({ state: State.idle });
    }
  }, [debouncedEmail, formError]);

  const handleEmailCheck = async (email: string) => {
    try {
      setResult({ state: State.validating });

      const res = await userApi.checkEmail({ email });

      const { suggestion, mailbox_exists: mailboxExists } = res.data;

      if (mailboxExists) {
        setResult({ state: State.success });
      } else if (!suggestion && !mailboxExists) {
        setResult({ state: State.warning });
      } else if (suggestion && !mailboxExists) {
        setResult({ state: State.suggestion, suggestedEmail: suggestion });
      }
    } catch {
      setResult({ state: State.idle });
    }
  };

  return result;
};
