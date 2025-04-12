import React from "react";

interface UnstyledInputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
  ref?: React.RefObject<HTMLInputElement | null>;
}

const UnstyledInput: React.FC<UnstyledInputProps> = ({
  className = "",
  ref,
  ...props
}) => {
  return <input ref={ref} className={className} {...props} />;
};

export default UnstyledInput;
