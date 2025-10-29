import s from "./BookPage.module.scss";
import { useParams } from "react-router-dom";
import { useCallback, useEffect, useState } from "react";
import { formatLanguage } from "../../../../common/helpers/helpers.ts";
import { BOOK_FORMATS } from "../../../../common/helpers/commonConstants.ts";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import { Trans } from "react-i18next";
import { Azw3, Epub, Fb2, Mobi, Pdf } from "../../../../assets/icons";
import BuySection from "../../../../components/CommonComponents/BuySection/BuySection.tsx";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { t } from "i18next";
import BackButton from "../../../../components/ui/BackButton/BackButton.tsx";
import { Path } from "../../../../routes/routes.ts";
import { mainApi } from "../../../../api/mainApi/mainApi.ts";
import PdfReaderWrapper from "../../../../components/CommonComponents/PdfReader/PdfReaderWrapper.tsx";

const BookPage = () => {
  const { bookId } = useParams();
  const [book, setBook] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchBookData = useCallback(async () => {
    try {
      const res = await mainApi.getBook(bookId);
      setBook(res.data);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  }, [bookId]);

  useEffect(() => {
    if (bookId) {
      fetchBookData();
    }
  }, [bookId, fetchBookData]);

  const handleProvideDownloadInfo = (
    currentFormat: string,
  ): { url: string | null; name: string | null } => {
    if (book) {
      const file = book.files_download?.find(
        (format: any) => format.file_format === currentFormat,
      );

      return { url: file?.download_url, name: book.title };
    }

    return { url: null, name: null };
  };

  return (
    <>
      <div className={s.book_page}>
        {loading && !book ? (
          <Loader />
        ) : (
          <>
            <section className={s.hero}>
              <BackButton link={Path.profileMain} />
              <h3>{book.title}</h3>
              <div className={s.content}>
                <div
                  className={`${s.left_side} ${!book.cover_url && s.no_picture}`}
                >
                  <img
                    src={book.cover_url || "/src/assets/no-pictures.png"}
                    alt="preview"
                  />
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
                    {book.publication_date && (
                      <p>
                        <Trans
                          i18nKey="bookLanding.publishedDate"
                          values={{ date: book.publication_date }}
                          components={[<span className={s.highlight} />]}
                        />
                      </p>
                    )}
                    {book.publisher && (
                      <p>
                        <Trans
                          i18nKey={"bookLanding.publisher"}
                          values={{
                            publisher: book.publisher,
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
                    formats={BOOK_FORMATS}
                    downloadInfo={handleProvideDownloadInfo}
                  />
                </div>
              </div>
            </section>
            <section id={"book-page-reader"} className={s.section_wrapper}>
              <SectionHeader name={t("profile.bookPage.readOnline")} />

              <PdfReaderWrapper
                fromProfile
                url={handleProvideDownloadInfo(BOOK_FORMATS[0]).url ?? ""}
                isSlideActive={true}
              />
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
