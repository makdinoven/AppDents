import { ReactNode } from "react";
import s from "./Form.module.scss";

interface FormProps {
  children: ReactNode;
  handleSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
}

const Form = ({ children, handleSubmit }: FormProps) => {
  return (
    <form className={s.form} onSubmit={handleSubmit}>
      {children}
    </form>
  );
};

export default Form;
