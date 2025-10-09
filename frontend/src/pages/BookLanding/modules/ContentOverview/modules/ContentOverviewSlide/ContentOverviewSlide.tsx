import { forwardRef, useImperativeHandle } from "react";
import s from "./ContentOverviewSlide.module.scss";
import PdfReaderWrapper from "../../../../../../components/CommonComponents/PdfReader/PdfReaderWrapper.tsx";
import { Bookmark } from "../../../../../../assets/icons";
import SectionHeader from "../../../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { t } from "i18next";
import { Trans } from "react-i18next";

interface ContentOverviewSlideProps {
  book: any;
  parentId: string;
  isActive: boolean;
  isSingle: boolean;
}

export interface ContentOverviewSlideRef {
  title: string;
}

const ContentOverviewSlide = forwardRef<
  ContentOverviewSlideRef,
  ContentOverviewSlideProps
>(({ book, parentId, isActive, isSingle }, ref) => {
  useImperativeHandle(ref, () => ({
    title: book?.title,
  }));
  return (
    <li className={`${s.slide} ${!isSingle && s.padding}`}>
      <div className={s.head}>
        {!isSingle && (
          <h3>
            <Bookmark />
            <span>{book?.title}</span>
          </h3>
        )}
      </div>
      <div className={s.content}>
        <PdfReaderWrapper
          isSlideActive={isActive}
          parentId={parentId}
          url={book?.preview_pdf_url}
        />
        <div className={s.description}>
          <span className={s.heading}>
            <SectionHeader name={t("bookLanding.description")} />
          </span>
          {book?.description || <Trans i18nKey="bookLanding.noDescription" />}
        </div>
      </div>
    </li>
  );
});

export default ContentOverviewSlide;
