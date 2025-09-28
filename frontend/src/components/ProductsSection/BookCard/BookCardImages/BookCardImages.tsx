import s from "./BookCardImages.module.scss";

const BookCardImages = ({ images }: { images: string[] }) => {
  return (
    <div className={s.images_wrapper}>
      {Array.from({ length: 5 }).map((_, i) => {
        const image = images[i];
        const zIndex = 5 - i;
        const bottom = 0;

        return image ? (
          <div
            key={i}
            style={{ zIndex, bottom }}
            className={`${s.img_wrapper} ${s[`overlay_${i}`]}`}
          >
            <img src={image} alt={`${i + 1}-image`} />
          </div>
        ) : (
          <div
            key={i}
            style={{ zIndex, bottom }}
            className={`${s.img_wrapper} ${s.no_photo} ${s[`overlay_${i}`]}`}
          />
        );
      })}
    </div>
  );
};

export default BookCardImages;
