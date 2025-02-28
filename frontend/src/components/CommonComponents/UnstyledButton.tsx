import React, { forwardRef } from "react";

interface UnstyledButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
}

const UnstyledButton = forwardRef<HTMLButtonElement, UnstyledButtonProps>(
  ({ children, className = "", ...props }, ref) => {
    return (
      <button ref={ref} className={className} {...props}>
        {children}
      </button>
    );
  },
);

export default UnstyledButton;
