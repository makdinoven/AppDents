import "swiper/swiper-bundle.css";
import s from "./BookHeroSkeleton.module.scss";

interface BookHeroSkeletonProps {
  type?: "download" | "buy";
}

const BookHeroSkeleton = ({ type = "download" }: BookHeroSkeletonProps) => {
  return (
    <section className={s.hero}>
      <h2 />
      <div className={s.content}>
        <div className={s.left_side} />
        <div className={s.right_side}>
          <div className={s.info}>
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
      </div>
    </section>
  );
};

export default BookHeroSkeleton;
