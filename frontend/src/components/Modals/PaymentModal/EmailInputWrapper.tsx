import { useEmailValidation } from "./useEmailValidation";
import Input from "../modules/Input/Input";
import {
  UseFormRegister,
  UseFormSetValue,
  UseFormWatch,
} from "react-hook-form";
import { PaymentType } from "../../../api/userApi/types";

interface EmailInputWrapperProps {
  name: "name" | "email" | "password";
  register: UseFormRegister<PaymentType>;
  watch: UseFormWatch<PaymentType>;
  setValue: UseFormSetValue<PaymentType>;
  error?: string;
  placeholder?: string;
}

const EmailInputWrapper: React.FC<EmailInputWrapperProps> = ({
  name,
  register,
  watch,
  setValue,
  error,
  placeholder,
}) => {
  const emailValue = watch(name);

  const result = useEmailValidation(emailValue);

  const handleSetSuggestion = (suggestion: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setValue(name, suggestion);
  };
  return (
    <Input
      id={name}
      placeholder={placeholder}
      error={error}
      state={result}
      onSuggestionTooltipClick={(suggestion, e) =>
        handleSetSuggestion(suggestion, e)
      }
      {...register(name)}
    />
  );
};

export default EmailInputWrapper;
