import axios from "axios";
import { useEffect, useState } from "react";
import useDebounce from "../../../../common/hooks/useDebounce";
import { userApi } from "../../../../api/userApi/userApi";
import {
  ProcessEmail,
  WarningEmail,
  ConfirmedEmail,
} from "../../../../assets/icons";

const stateIndicators = {
  idle: null,
  success: <ConfirmedEmail />,
  validating: <ProcessEmail />,
  suggestion: <WarningEmail />,
  warning: <WarningEmail />,
};

export const useEmailValidation = (email: string, delay: number = 300) => {
  const [state, setState] = useState<
    "idle" | "success" | "validating" | "suggestion" | "warning"
  >("idle");
  const [error, setError] = useState<string | null>(null);

  const debouncedEmail = useDebounce(email, delay);

  useEffect(() => {
    if (!debouncedEmail) {
      setState("idle");
      setError(null);
      return;
    }
    setState("validating");
    setError(null);

    handleEmailCheck(debouncedEmail);
  }, [debouncedEmail]);

  const handleEmailCheck = async (email: string) => {
    try {
      const res = await userApi.checkEmail({ email });

      const isSyntacticallyValid = res.data.is_syntactically_valid;
      const suggestion = res.data.suggestion;
      const mailboxExists = res.data.mailbox_exists;

      if (mailboxExists) {
        console.log("success");
        setState("success");
      } else if (
        (isSyntacticallyValid && !suggestion && !mailboxExists) ||
        !isSyntacticallyValid
      ) {
        console.log("warning");
        setState("warning");
      } else if (isSyntacticallyValid && suggestion && !mailboxExists) {
        console.log("suggestion");
        setState("suggestion");
      }

      console.log({ ...res.data, email });
    } catch (error) {
      if (error instanceof Error || axios.isAxiosError(error))
        setError(error.message);
    }
  };

  const currentIndicator = stateIndicators[state];
  return { currentIndicator };
};
