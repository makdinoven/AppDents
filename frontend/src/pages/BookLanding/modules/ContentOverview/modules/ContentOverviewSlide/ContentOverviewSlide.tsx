import React from "react";
import s from "./ContentOverviewSlide.module.scss";
import PdfReaderWrapper from "../../../../../../components/CommonComponents/PdfReader/PdfReaderWrapper.tsx";

interface ContentOverviewSlideProps {
  book: any;
  index: number;
  parentId: string;
}

const ContentOverviewSlide: React.FC<ContentOverviewSlideProps> = ({
  book,
  index,
  parentId,
}: ContentOverviewSlideProps) => {
  const description =
    " This book provides a comprehensive and evidence-based overview of\n" +
    "          current advances and challenges in modern medicine. Combining clinical\n" +
    "          experience with the latest scientific research, it offers valuable\n" +
    "          insights into diagnosis, treatment, and prevention strategies across a\n" +
    "          wide range of medical fields. Designed for medical professionals,\n" +
    "          researchers, and students, the book covers key topics such as\n" +
    "          patient-centered care, innovations in medical technology, public\n" +
    "          health issues, and ethical considerations in clinical practice. Each\n" +
    "          chapter is authored by leading experts and includes real-world case\n" +
    "          studies, updated guidelines, and critical reflections on future\n" +
    "          developments in healthcare. Whether used as a textbook, a reference\n" +
    "          guide, or a source for professional development, this publication is\n" +
    "          an essential resource for anyone involved in the rapidly evolving\n" +
    "          landscape of global medicine.";

  return (
    <li className={s.slide}>
      <h3>
        <span>{index + 1}. </span>
        <span>{book.title}</span>
      </h3>
      <div className={s.content}>
        <PdfReaderWrapper parentId={parentId} url={book.preview_pdf_url} />
        <p className={s.description}>{description}</p>
      </div>
    </li>
  );
};

export default ContentOverviewSlide;
