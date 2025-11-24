import s from "./LoaderOverlay.module.scss";

const LoaderOverlay = ({ inset }: { inset?: number }) => {
  return (
    <div style={{ inset: `-${inset}px` }} className={s.loader_overlay}></div>
  );
};

export default LoaderOverlay;
