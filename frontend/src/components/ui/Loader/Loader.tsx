import s from "./Loader.module.scss";

const Loader = ({ className }: { className?: string }) => {
  return <span className={`${s.loader_twoDots} ${className}`}></span>;
};

export default Loader;
