import { useEffect, useState } from "react";
import s from "./BookCardImages.module.scss";

const INTERVAL = 1000;

const BookCardImages = ({
  images,
  color,
  single,
}: {
  images: string[];
  color?: string;
  single?: boolean;
}) => {
  const safeImages = images ?? [];
  const [hover, setHover] = useState(false);
  const [shift, setShift] = useState(0);
  const realImages = safeImages.filter(Boolean).slice(0, 4);

  useEffect(() => {
    if (single) return;

    let interval: NodeJS.Timeout;
    if (hover) {
      interval = setInterval(() => {
        setShift((prev) => (prev + 1) % realImages.length);
      }, INTERVAL);
    } else {
      setShift(0);
    }
    return () => clearInterval(interval);
  }, [hover, single]);

  if (single) {
    const mainImage = realImages[0];
    return (
      <div className={`${s.images_wrapper} ${color ? s[color] : ""}`}>
        {mainImage ? (
          <div className={`${s.img_wrapper} ${s.single} ${s.active}`}>
            <img src={mainImage} alt="main-image" />
          </div>
        ) : (
          <div className={`${s.img_wrapper} ${s.single} ${s.no_photo}`} />
        )}
      </div>
    );
  }

  return (
    <div
      className={s.images_wrapper}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      {Array.from({ length: 4 }).map((_, i) => {
        const image = safeImages[i];
        const zIndex = 4 - i;
        const offset = i < shift ? -156 : 0;
        const style = {
          zIndex,
          transform: `translateX(${offset}px)`,
        };
        const isActive = i === shift;

        return image ? (
          <div
            key={i}
            style={style}
            className={`${s.img_wrapper} ${color ? s[color] : ""} ${isActive ? s.active : ""}`}
          >
            <img src={image} alt={`${i + 1}-image`} />
          </div>
        ) : (
          <div
            key={i}
            style={{ zIndex, opacity: 1 - 0.2 * i }}
            className={`${s.img_wrapper} ${s.no_photo}`}
          />
        );
      })}
      {realImages.length > 1 && (
        <div className={`${s.bullets} ${color ? s[color] : ""}`}>
          {realImages.map((_, i) => (
            <div
              key={i}
              onMouseEnter={() => setHover(false)}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setShift(i);
              }}
              className={`${s.bullet} ${i === shift ? s.active : ""}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default BookCardImages;
