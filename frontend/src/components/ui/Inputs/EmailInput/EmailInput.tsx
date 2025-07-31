import Input from "../Input/Input.tsx";
import { ErrorIcon } from "../../../../assets/icons";
import InputTooltip from "../../InputTooltip/InputTooltip.tsx";
import { useEmailValidation } from "../../../../common/hooks/useEmailValidation.tsx";

interface EmailInputProps {
  name: "email";
  id: string;
  error?: string;
  placeholder?: string;
  isValidationUsed: boolean;
  value?: string;
  setValue?: any;
}

const EmailInput = ({
  id,
  error,
  placeholder,
  setValue,
  value,
  isValidationUsed,
  ...props
}: EmailInputProps) => {
  const name = "email";
  const { state, suggestedEmail } = useEmailValidation(value, !!error);

  const showFormError = !!error;
  const showValidation =
    isValidationUsed && !error && (!!state.icon || !!state.msg);

  const tooltipProps = showFormError
    ? {
        type: "error" as const,
        icon: <ErrorIcon />,
        visible: !!error,
        textKey: error,
        tooltipCondition: true,
        suggestedEmail: undefined,
        onTooltipClick: undefined,
      }
    : {
        type: state.name,
        visible: showValidation,
        icon: state.icon,
        textKey: state.msg,
        tooltipCondition: !!state.msg,
        suggestedEmail,
        onTooltipClick: (email: string | null) =>
          email ? setValue?.(name, email) : null,
      };

  return (
    <>
      <Input
        id={id}
        error={error}
        iconPadding={showValidation}
        placeholder={placeholder}
        {...props}
      >
        {tooltipProps && <InputTooltip {...tooltipProps} />}
      </Input>
    </>
  );
};

export default EmailInput;
