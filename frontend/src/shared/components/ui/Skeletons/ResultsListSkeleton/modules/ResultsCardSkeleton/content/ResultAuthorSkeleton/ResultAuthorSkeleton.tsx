import s from "./ResultAuthorSkeleton.module.scss";

const ResultAuthorSkeleton = () => {
  return (
    <>
      <div className={s.photo_wrapper}>
        <div className={s.language_placeholder} />
        <div className={s.photo_placeholder} />
      </div>
      <div className={s.card_body}>
        <h5 className={s.name_placeholder} />
        <div className={s.count_items}>
          {/*<div />*/}
          <div />
        </div>
        <p className={s.description} />
        <button className={s.button} />
      </div>
    </>
  );
};

export default ResultAuthorSkeleton;
