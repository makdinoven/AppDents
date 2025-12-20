import s from "./BookPage.module.scss";
import { useParams } from "react-router-dom";
import { JSX, useCallback, useEffect, useState } from "react";
import { formatLanguage } from "../../../../shared/common/helpers/helpers.ts";
import { BASE_URL } from "../../../../shared/common/helpers/commonConstants.ts";
import { Trans } from "react-i18next";
import { Azw3, Epub, Fb2, Mobi, Pdf } from "../../../../shared/assets/icons";
import SectionHeader from "../../../../shared/components/ui/SectionHeader/SectionHeader.tsx";
import { t } from "i18next";
import BackButton from "../../../../shared/components/ui/BackButton/BackButton.tsx";
import { mainApi } from "../../../../shared/api/mainApi/mainApi.ts";
import BookHeroSkeleton from "../../../../shared/components/ui/Skeletons/BookHeroSkeleton/BookHeroSkeleton.tsx";
import PdfReader from "../../../../shared/components/PdfReader/PdfReader.tsx";
import { rewriteCdnLinkToMedia } from "../../../../shared/common/helpers/helpers.ts";
import DownloadSection from "./DownloadSection/DownloadSection.tsx";
import { NoPictures } from "../../../../shared/assets";
import { PATHS } from "../../../../app/routes/routes.ts";

const BookPage = () => {
  const { id } = useParams();
  const [book, setBook] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const pdf_link = `${BASE_URL}/api/books/${id}/pdf`;

  const fetchBookData = useCallback(async () => {
    try {
      const res = await mainApi.getBook(id);
      setBook(res.data);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      console.error(error);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      fetchBookData();
    }
  }, [id, fetchBookData]);

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

  return (
    <>
      <div className={s.book_page}>
        {loading && !book ? (
          <BookHeroSkeleton type="download" />
        ) : (
          <>
            <section className={s.hero}>
              <BackButton link={PATHS.PROFILE} />
              <h3>{book.title}</h3>
              <div className={s.content}>
                <div className={s.left_side}>
                  {book.cover_url ? (
                    <img src={book.cover_url} alt="preview" />
                  ) : (
                    <NoPictures />
                  )}
                </div>
                <div className={s.right_side}>
                  <div className={s.info}>
                    {book.language && (
                      <p>
                        <Trans
                          i18nKey={"bookLanding.language"}
                          values={{
                            language: formatLanguage(book.language),
                          }}
                          components={[<span className={s.highlight} />]}
                        />
                      </p>
                    )}
                    {book.authors?.length > 0 && (
                      <p>
                        <Trans
                          i18nKey={`${book.authors?.length > 1 ? "bookLanding.authors" : "bookLanding.author"}`}
                          values={{
                            authors: book.authors
                              ?.map((author: any) => author.name)!
                              .join(", "),
                          }}
                          components={[<span className={s.highlight} />]}
                        />
                      </p>
                    )}
                    {book.publishers?.length > 0 && (
                      <p>
                        <Trans
                          i18nKey="bookLanding.publisher"
                          values={{
                            publisher: book.publishers
                              ?.map((publisher: any) => publisher.name)!
                              .join(", "),
                          }}
                          components={[<span className={s.highlight} />]}
                        />
                      </p>
                    )}
                    {book.publication_date && (
                      <p>
                        <Trans
                          i18nKey="bookLanding.publicationDate"
                          values={{ date: book.publication_date }}
                          components={[<span className={s.highlight} />]}
                        />
                      </p>
                    )}
                    {book.page_count && (
                      <p>
                        <Trans
                          i18nKey={"bookLanding.pages.count"}
                          values={{
                            count: book.page_count,
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
                        {book.available_formats?.map((format: any) => (
                          <span key={format}>{getFormatIcon(format)}</span>
                        ))}
                      </span>
                    </p>
                  </div>
                  <DownloadSection formats={book.files_download} />
                </div>
              </div>
            </section>
            <section id={"book-page-reader"} className={s.section_wrapper}>
              <SectionHeader name={t("profile.bookPage.readOnline")} />

              <PdfReader
                fromProfile
                url={pdf_link ? rewriteCdnLinkToMedia(pdf_link) : null}
              />
              {pdf_link && (
                <p className={s.failed_to_load}>
                  {t("readerFailedToLoad")}{" "}
                  <a
                    href={rewriteCdnLinkToMedia(pdf_link)}
                    target="_blank"
                    className="highlight"
                    rel="noopener noreferrer"
                  >
                    {t("watchHere")}
                  </a>
                </p>
              )}
            </section>
            {/*<section className={s.section_wrapper}>*/}
            {/*  <SectionHeader name={t("profile.bookPage.listenInAudioVerse")} />*/}
            {/*  <div className={s.audios_section}></div>*/}
            {/*</section>*/}
          </>
        )}
      </div>
    </>
  );
};

export default BookPage;
