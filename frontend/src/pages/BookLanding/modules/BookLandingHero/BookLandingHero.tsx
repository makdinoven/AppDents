import React, { JSX } from "react";
import s from "./BookLandingHero.module.scss";
import { Trans } from "react-i18next";
import BuySection from "../../../../components/CommonComponents/BuySection/BuySection.tsx";
import { Azw3, Epub, Fb2, Mobi, Pdf } from "../../../../assets/icons";
import { BOOK_FORMATS } from "../../../../common/helpers/commonConstants.ts";
import BookHeroSkeleton from "../../../../components/ui/Skeletons/BookHeroSkeleton/BookHeroSkeleton.tsx";
import { formatLanguage } from "../../../../common/helpers/helpers.ts";
import { t } from "i18next";

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
  const formatIcons: Record<string, JSX.Element> = {
    PDF: <Pdf />,
    EPUB: <Epub />,
    MOBI: <Mobi />,
    AZW3: <Azw3 />,
    FB2: <Fb2 />,
  };

  const getFormatIcon = (format: string) => {
    return formatIcons[format.toUpperCase()] ?? null;
  };

  console.log(data);

  return loading ? (
    <BookHeroSkeleton type="buy" />
  ) : (
    <section className={s.hero}>
      <h3>{data.landing_name}</h3>
      <div className={s.content}>
        <div
          className={`${s.left_side} ${!data.books?.[0]?.cover_url && s.no_picture}`}
        >
          <img
            src={data.books?.[0]?.cover_url || "/src/assets/no-pictures.png"}
            alt="preview"
          />
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
            {data.books?.length > 0 && data.books[0].publishers?.length > 0 && (
              <p>
                <Trans
                  i18nKey={"bookLanding.publisher"}
                  values={{
                    publisher: data.books[0].publishers[0].name,
                  }}
                  components={[<span className={s.highlight} />]}
                />
              </p>
            )}
            {data.books?.length > 0 && (
              <p>
                <Trans
                  i18nKey="bookLanding.publicationDate"
                  values={{ date: data.books[0].publication_date }}
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
                  components={[<span className={s.highlight} />]}
                />
              </p>
            )}
            <p>
              <Trans
                i18nKey={"bookLanding.salesCount"}
                values={{
                  count: data.sales_count,
                }}
                components={[<span className={s.highlight} />]}
              />
            </p>
            {data.tags?.length > 0 && (
              <p>
                <Trans
                  i18nKey="bookLanding.tags"
                  values={{
                    tags: data.tags?.map((tag: any) => t(tag))!.join(", "),
                  }}
                  components={[<span className={s.highlight} />]}
                />
              </p>
            )}
            <p className={s.formats_field}>
              <span>
                <Trans i18nKey="bookLanding.availableFormats" />
              </span>
              <span className={s.formats}>
                {data.available_formats?.map((format: any) => (
                  <span key={format}>{getFormatIcon(format)}</span>
                ))}
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
