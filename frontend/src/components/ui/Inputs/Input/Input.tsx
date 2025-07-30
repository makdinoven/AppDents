import React, { ReactNode } from "react";
import s from "./Input.module.scss";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string | boolean;
  children?: ReactNode;
  iconPadding?: boolean;
}

const Input: React.FC<InputProps> = ({
  error,
  type,
  iconPadding,
  children,
  ...props
}) => {
  return (
    <div
      className={`${s.input_wrapper} ${error ? s.error : ""} ${type ? s[type] : ""} ${iconPadding ? s.padding : ""}`}
    >
      <input {...props} type={type} />

      {children}
    </div>
  );
};

export default Input;
