import React from "react";

interface UnstyledInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

const UnstyledInput: React.FC<UnstyledInputProps> = ({
  className = "",
  ...props
}) => {
  return <input className={className} {...props} />;
};

export default UnstyledInput;
