import s from "./LineWrapper.module.scss";

const LineWrapper = ({
  hasArrow,
  children,
}: {
  hasArrow?: boolean;
  children: any;
}) => {
  return (
    <div className={s.btn_wrapper}>
      {children} {hasArrow ? "" : ""}
    </div>
  );
};

export default LineWrapper;
