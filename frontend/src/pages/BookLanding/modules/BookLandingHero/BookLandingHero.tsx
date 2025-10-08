import React from "react";
import s from "./BookLandingHero.module.scss";
import { Trans } from "react-i18next";
import BuySection from "../../../../components/CommonComponents/BuySection/BuySection.tsx";
import { Azw3, Epub, Fb2, Mobi, Pdf } from "../../../../assets/icons";
import { BOOK_FORMATS } from "../../../../common/helpers/commonConstants.ts";
import BookHeroSkeleton from "../../../../components/ui/Skeletons/BookHeroSkeleton/BookHeroSkeleton.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../store/store.ts";

interface LandingHeroProps {
  data: any;
  loading: boolean;
}

const BookLandingHero: React.FC<LandingHeroProps> = ({
  data,
  loading,
}: LandingHeroProps) => {
  const { language } = useSelector((state: AppRootStateType) => state.user);
  return loading ? (
    <BookHeroSkeleton type="buy" />
  ) : (
    <section className={s.hero}>
      <h3>{data.landing_name}</h3>
      <div className={s.content}>
        <div className={s.left_side}>
          <img src={data.gallery[0].url} alt="preview" />
        </div>
        <div className={s.right_side}>
          <div className={s.info}>
            <p>
              <Trans
                i18nKey={"bookLanding.language"}
                values={{
                  language: language.toLowerCase(),
                }}
                components={[<span className={s.highlight} />]}
              />
            </p>
            <p>
              <Trans
                i18nKey={`${data.authors?.length > 1 ? "bookLanding.authors" : "bookLanding.author"}`}
                values={{
                  authors: data.authors
                    ?.map((author: any) => author.name)!
                    .join(", "),
                }}
                components={[<span className={s.highlight} />]}
              />
            </p>
            <p>
              <Trans
                i18nKey="bookLanding.publishedDate"
                values={{ date: data?.publication_date }}
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
            type="buy"
            formats={BOOK_FORMATS}
            oldPrice={data?.old_price}
            newPrice={data?.new_price}
          />
        </div>
      </div>
    </section>
  );
};

export default BookLandingHero;
