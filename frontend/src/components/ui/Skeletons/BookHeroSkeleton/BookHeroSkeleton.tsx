import "swiper/swiper-bundle.css";
import s from "./BookHeroSkeleton.module.scss";

interface BookHeroSkeletonProps {
  type?: "download" | "buy";
}

const BookHeroSkeleton = ({ type = "download" }: BookHeroSkeletonProps) => {
  return (
    <section className={s.hero}>
      <div className={s.left_side}>
        <div className={s.lang_price}>
          <div className={s.price} />
          <div className={s.lang} />
        </div>
        <div className={s.slider}>
          <ul className={s.gallery}>
            {Array(4)
              .fill({ length: 4 })
              .map((_, index) => (
                <li key={index} />
              ))}
          </ul>
          <div className={s.preview_photo} />
        </div>
      </div>
      <div className={s.right_side}>
        <div className={s.info}>
          <h2 />
          <p />
          <p className={s.formats_field} />
        </div>
        <div className={s.section_wrapper}>
          <section className={s.buy_section}>
            <p />
            <div className={s.button} />
            {type === "download" && (
              <ul className={s.format_buttons}>
                {Array(5)
                  .fill({ length: 5 })
                  .map((_, index) => {
                    return <li key={index} />;
                  })}
              </ul>
            )}
          </section>
        </div>
      </div>
    </section>
  );
};

export default BookHeroSkeleton;
