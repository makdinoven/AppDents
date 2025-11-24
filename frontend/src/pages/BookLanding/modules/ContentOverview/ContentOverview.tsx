import React from "react";
import s from "./ContentOverview.module.scss";
import SectionHeader from "../../../../shared/components/ui/SectionHeader/SectionHeader.tsx";
import { t } from "i18next";
import { Trans } from "react-i18next";
import PdfReader from "../../../../shared/components/PdfReader/PdfReader.tsx";
import { Bookmark } from "../../../../shared/assets/icons";

interface ContentOverviewProps {
  books: any[];
}

const ContentOverview: React.FC<ContentOverviewProps> = ({
  books,
}: ContentOverviewProps) => {
  return (
    <div id={"book-pages"} className={s.content_overview}>
      {books.length > 1 && (
        <SectionHeader name={t("bookLanding.contentOverview")} />
      )}
      <ul className={s.books}>
        {books.map((book: any, i) => (
          <li key={`${book.title}-${i}`} className={s.book_container}>
            {books.length > 1 && (
              <h3 className={s.book_title}>
                <Bookmark />
                <span>{book?.title}</span>
              </h3>
            )}

            <div className={s.content}>
              <PdfReader url={book?.preview_pdf_url} fromProfile={false} />
              <div className={s.description}>
                <span className={s.heading}>
                  <SectionHeader name={t("bookLanding.description")} />
                </span>
                {book?.description || (
                  <Trans i18nKey="bookLanding.noDescription" />
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ContentOverview;
