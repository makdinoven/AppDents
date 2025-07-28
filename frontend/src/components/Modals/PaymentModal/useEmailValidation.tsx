import { ReactNode } from "react";
import { useLayoutEffect, useState } from "react";
import useDebounce from "../../../common/hooks/useDebounce";
import { userApi } from "../../../api/userApi/userApi";
import {
  ProcessEmail,
  WarningEmail,
  ConfirmedEmail,
} from "../../../assets/icons";

const warningEmail = <WarningEmail />;

const State = {
  idle: "idle",
  success: "success",
  validating: "validating",
  suggestion: "suggestion",
  warning: "warning",
} as const;

const stateIndicators: Record<keyof typeof State, ReactNode | null> = {
  idle: null,
  success: <ConfirmedEmail />,
  validating: <ProcessEmail />,
  suggestion: warningEmail,
  warning: warningEmail,
};

interface useEmailValidationResult {
  state: keyof typeof State;
  currentIndicator: ReactNode | null;
  suggestedEmail: string;
}

export const useEmailValidation = (
  email: string,
  delay: number = 300
): useEmailValidationResult => {
  const [result, setResult] = useState<useEmailValidationResult>({
    state: "idle",
    currentIndicator: null,
    suggestedEmail: "",
  });

  const debouncedEmail = useDebounce(email, delay);

  useLayoutEffect(() => {
    if (!debouncedEmail) {
      setResult((prev) => ({
        ...prev,
        state: State.idle,
        currentIndicator: stateIndicators[State.idle],
        suggestedEmail: "",
      }));
      return;
    }

    handleEmailCheck(debouncedEmail);
  }, [debouncedEmail]);

  const handleEmailCheck = async (email: string) => {
    try {
      setResult((prev) => ({
        ...prev,
        state: State.validating,
        currentIndicator: stateIndicators[State.validating],
        suggestedEmail: "",
      }));

      const res = await userApi.checkEmail({ email });

      const {
        is_syntactically_valid: isSyntacticallyValid,
        suggestion,
        mailbox_exists: mailboxExists,
      } = res.data;

      if (mailboxExists) {
        setResult((prev) => ({
          ...prev,
          state: State.success,
          currentIndicator: stateIndicators[State.success],
          suggestedEmail: "",
        }));
      } else if (
        (isSyntacticallyValid && !suggestion && !mailboxExists) ||
        (!isSyntacticallyValid && debouncedEmail.includes("@"))
      ) {
        setResult((prev) => ({
          ...prev,
          state: State.warning,
          currentIndicator: stateIndicators[State.warning],
          suggestedEmail: "",
        }));
      } else if (isSyntacticallyValid && suggestion && !mailboxExists) {
        suggestion !== null &&
          setResult((prev) => ({
            ...prev,
            state: State.suggestion,
            currentIndicator: stateIndicators[State.suggestion],
            suggestedEmail: suggestion,
          }));
      }

      console.log({ isSyntacticallyValid, suggestion, mailboxExists, email });
    } catch (error) {}
  };

  return result;
};
