import s from "./ResultLandingSkeleton.module.scss";
import { SearchResultKeysType } from "../../../../../../../../store/slices/mainSlice.ts";

const ResultLandingSkeleton = ({
  type,
}: {
  type: Exclude<SearchResultKeysType, "authors">;
}) => {
  return (
    <>
      <div
        className={`${s.photo_placeholder} ${type === "book_landings" && s.book}`}
      />
      <div className={s.content}>
        <div className={s.content_header}>
          <div className={s.prices}>
            <div className={s.language_placeholder} />
            <span className={s.new_price} />
            <span className={s.old_price} />
          </div>
          <div className={s.cart_btn} />
        </div>
        <p className={s.name} />
        <p className={s.authors} />
      </div>
    </>
  );
};

export default ResultLandingSkeleton;
