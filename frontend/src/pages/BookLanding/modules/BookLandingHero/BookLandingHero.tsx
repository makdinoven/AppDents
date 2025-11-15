import React from "react";
import s from "./BookLandingHero.module.scss";
import { Trans } from "react-i18next";
import BuySection from "../../../../components/CommonComponents/BuySection/BuySection.tsx";
import { Azw3, Epub, Fb2, Mobi, Pdf } from "../../../../assets/icons";
import { BOOK_FORMATS } from "../../../../common/helpers/commonConstants.ts";
import BookHeroSkeleton from "../../../../components/ui/Skeletons/BookHeroSkeleton/BookHeroSkeleton.tsx";
import { formatLanguage } from "../../../../common/helpers/helpers.ts";
import { NoPictures } from "../../../../assets";

interface LandingHeroProps {
  data: any;
  loading: boolean;
  openPayment: () => void;
}

const BookLandingHero: React.FC<LandingHeroProps> = ({
  data,
  loading,
  openPayment,
}: LandingHeroProps) => {
  return loading ? (
    <BookHeroSkeleton type="buy" />
  ) : (
    <section className={s.hero}>
      <h3>{data.landing_name}</h3>
      <div className={s.content}>
        <div className={s.left_side}>
          {data.books?.[0]?.cover_url ? (
            <img src={data.books[0].cover_url} alt="preview" />
          ) : (
            <NoPictures />
          )}
        </div>
        <div className={s.right_side}>
          <div className={s.info}>
            {data.language && (
              <p>
                <Trans
                  i18nKey={"bookLanding.language"}
                  values={{
                    language: formatLanguage(data.language),
                  }}
                  components={[<span className={s.highlight} />]}
                />
              </p>
            )}
            {data.authors?.length > 0 && (
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
            )}
            {data.publication_date && (
              <p>
                <Trans
                  i18nKey="bookLanding.publishedDate"
                  values={{ date: data.publication_date }}
                  components={[<span className={s.highlight} />]}
                />
              </p>
            )}
            {data.books[0].publisher && (
              <p>
                <Trans
                  i18nKey={"bookLanding.publisher"}
                  values={{
                    publisher: data.books[0].publisher,
                  }}
                  components={[<span className={s.highlight} />]}
                />
              </p>
            )}
            {data.total_pages && (
              <p>
                <Trans
                  i18nKey={"bookLanding.pages.count"}
                  values={{
                    count: data.total_pages,
                  }}
                />
              </p>
            )}
            {/*{!!data.sales_count && (*/}
            <p>
              <Trans
                i18nKey={"bookLanding.salesCount"}
                values={{
                  count: data.sales_count,
                }}
              />
            </p>
            {/*)}*/}
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
            openPayment={openPayment}
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
