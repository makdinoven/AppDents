import React, { ReactNode } from "react";
import s from "./Input.module.scss";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string | boolean;
  children?: ReactNode;
  iconPadding?: boolean;
  variant?: "admin" | "invite";
}

const Input: React.FC<InputProps> = ({
  error,
  type,
  iconPadding,
  children,
  variant,
  ...props
}) => {
  return (
    <div
      className={`${s.input_wrapper} ${error ? s.error : ""} ${type ? s[type] : ""} ${iconPadding ? s.padding : ""} ${variant ? s[variant] : ""} `}
    >
      <input {...props} type={type} className={variant ? s[variant] : ""} />

      {children}
    </div>
  );
};

export default Input;
