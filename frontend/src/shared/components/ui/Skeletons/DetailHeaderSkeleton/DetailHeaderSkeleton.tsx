import s from "./DetailHeaderSkeleton.module.scss";
import BackButton from "../../BackButton/BackButton.tsx";

const DetailHeaderSkeleton = () => {
  return (
    <div>
      <BackButton />
      <div className={s.skeleton}></div>
    </div>
  );
};

export default DetailHeaderSkeleton;
