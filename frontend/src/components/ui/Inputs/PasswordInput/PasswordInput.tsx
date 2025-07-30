import Input from "../Input/Input.tsx";
import { ErrorIcon, EyeClosed, EyeOpened } from "../../../../assets/icons";
import s from "./PasswordInput.module.scss";
import { useState } from "react";
import InputTooltip from "../../InputTooltip/InputTooltip.tsx";

const PasswordInput = ({
  id,
  error,
  placeholder,
  ...props
}: {
  id: string;
  error?: string;
  placeholder: string;
}) => {
  const [visible, setVisible] = useState(false);
  const inputType = visible ? "text" : "password";

  return (
    <>
      <Input
        id={id}
        error={error}
        placeholder={placeholder}
        type={inputType}
        {...props}
      >
        <button
          type="button"
          className={`${s.eye} ${error ? s.error : ""}`}
          onClick={() => setVisible((prev) => !prev)}
          tabIndex={-1}
        >
          {visible ? <EyeClosed /> : <EyeOpened />}
        </button>

        <InputTooltip
          type={"error"}
          visible={!!error}
          tooltipCondition={!!error}
          icon={<ErrorIcon />}
          textKey={error}
        />
      </Input>
    </>
  );
};

export default PasswordInput;
