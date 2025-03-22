import s from "./Loader.module.scss";

const Loader = ({ variant }: { variant?: "threeDots" | "twoDots" }) => {
  switch (variant) {
    case "threeDots":
      return <span className={s.loader_threeDots}></span>;
      break;
    case "twoDots":
      return <span className={s.loader_twoDots}></span>;
      break;
    default:
      return <span className={s.loader_twoDots}></span>;
  }
};

export default Loader;
