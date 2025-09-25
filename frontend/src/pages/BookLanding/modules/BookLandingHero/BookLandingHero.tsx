import React from "react";
import s from "./BookLandingHero.module.scss";
import { Trans } from "react-i18next";
import HeroSlider from "./modules/HeroSlider/HeroSlider.tsx";
import BuySection from "../../../../components/CommonComponents/BuySection/BuySection.tsx";
import { En, Pdf, Epub, Mobi, Azw3, Fb2 } from "../../../../assets/icons";
import { FORMATS } from "../../../../common/helpers/commonConstants.ts";
import Loader from "../../../../components/ui/Loader/Loader.tsx";

interface LandingHeroProps {
  data: any;
  loading: boolean;
}

const BookLandingHero: React.FC<LandingHeroProps> = ({
  data,
  loading,
}: LandingHeroProps) => {
  const authors = data.authors?.map((author: any) => author.name);
  return loading ? (
    <Loader />
  ) : (
    <section className={s.hero}>
      <div className={s.left_side}>
        <div className={s.lang_price}>
          <div className={s.price}>
            <span className={s.new_price}>${data.new_price}</span>
            <span className={s.old_price}>${data.old_price}</span>
          </div>
          <En />
        </div>
        <HeroSlider gallery={data.gallery} />
      </div>
      <div className={s.right_side}>
        <div className={s.info}>
          <h2>{data.landing_name}</h2>
          <p>
            <Trans
              i18nKey={`${data.authors?.length > 1 ? "bookLanding.authors" : "bookLanding.author"}`}
              values={{ authors: authors!.join(", ") }}
              components={[<span className={s.highlight} />]}
            />
          </p>
          <p className={s.formats_field}>
            <span>
              <Trans i18nKey="bookLanding.availableFormats" />
            </span>
            <span className={s.formats}>
              <Pdf />
              <Epub />
              <Mobi />
              <Azw3 />
              <Fb2 />
            </span>
          </p>
        </div>
        <BuySection
          type="download"
          formats={FORMATS}
          oldPrice={data.old_price}
          newPrice={data.new_price}
        />
      </div>
    </section>
  );
};

export default BookLandingHero;
