import React from "react";
import s from "./Title.module.scss";
interface TitleProps {
  children: React.ReactNode;
  className?: string;
}

const Title: React.FC<TitleProps> = ({ children, className = "" }) => {
  return <h1 className={`${className} ${s.title}`}>{children}</h1>;
};

export default Title;
