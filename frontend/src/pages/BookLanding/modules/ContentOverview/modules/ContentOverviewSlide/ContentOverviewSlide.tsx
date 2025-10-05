import { forwardRef, useImperativeHandle } from "react";
import s from "./ContentOverviewSlide.module.scss";
import PdfReaderWrapper from "../../../../../../components/CommonComponents/PdfReader/PdfReaderWrapper.tsx";
import { Trans } from "react-i18next";
import { Bookmark } from "../../../../../../assets/icons";

interface ContentOverviewSlideProps {
  book: any;
  parentId: string;
  isActive: boolean;
}

export interface ContentOverviewSlideRef {
  title: string;
}

const ContentOverviewSlide = forwardRef<
  ContentOverviewSlideRef,
  ContentOverviewSlideProps
>(({ book, parentId, isActive }, ref) => {
  useImperativeHandle(ref, () => ({
    title: book.title,
  }));

  return (
    <li className={s.slide}>
      <div className={s.head}>
        <h3>
          <Bookmark />
          <span>{book.title}</span>{" "}
        </h3>
        {book.title && (
          <div className={s.date}>
            <span>•</span>
            <span>
              <Trans
                i18nKey="bookLanding.publishedDate"
                values={{ date: book.publication_date }}
                components={[<span className={s.highlight} />]}
              />
            </span>
          </div>
        )}
      </div>
      <div className={s.content}>
        <PdfReaderWrapper
          isSlideActive={isActive}
          parentId={parentId}
          url={book.preview_pdf_url}
        />
        <p className={s.description}>{book.description}</p>
      </div>
    </li>
  );
});

export default ContentOverviewSlide;
