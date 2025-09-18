import { useEffect, useState } from "react";
import { Document, Thumbnail } from "react-pdf";
import s from "./ThumbNails.module.scss";
import { PDFDocumentProxy } from "pdfjs-dist";

type Options = {
  cMapUrl: string;
  standardFontDataUrl: string;
  wasmUrl: string;
};

interface IThumbNailsProps {
  isOpen: boolean;
  onLoadSuccess: ({ numPages }: PDFDocumentProxy) => void;
  options: Options;
  totalPages: number | undefined;
  link: string;
  handlePageChange: (currentPage: number) => void;
  onClick: (e: React.MouseEvent<HTMLInputElement>) => void;
  currentPage: number;
}

const ThumbNails = ({
  isOpen,
  onLoadSuccess,
  options,
  totalPages,
  link,
  handlePageChange,
  onClick,
  currentPage,
}: IThumbNailsProps) => {
  const [activeThumbNail, setActiveThumbNail] = useState(1);

  useEffect(() => {
    setActiveThumbNail(currentPage);
  }, [currentPage]);

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
  };

  const handleThumbNailClick = (currentPage: number) => {
    handlePageChange(currentPage);
    setActiveThumbNail(currentPage);
  };

  return (
    <div
      className={`${s.thumb_nails_wrapper} ${isOpen && s.open}`}
      onContextMenu={handleContextMenu}
      onClick={onClick}
    >
      <Document
        file={link}
        onLoadSuccess={onLoadSuccess}
        loading=""
        error=""
        options={options}
        className={s.thumb_nails_document}
      >
        <ul className={s.thumb_nails_list}>
          {Array.from({ length: totalPages as number }, (_, i) => {
            const currentPage = i + 1;
            return (
              <li key={currentPage} className={s.thumb_nail_wrapper}>
                <Thumbnail
                  pageNumber={currentPage}
                  width={100}
                  canvasBackground="white"
                  className={`${s.thumb_nail} ${activeThumbNail === currentPage && s.active}`}
                  onClick={() => handleThumbNailClick(currentPage)}
                  renderMode="canvas"
                  loading="lazy"
                />
                <span className={s.page}>{currentPage}</span>
              </li>
            );
          })}
        </ul>
      </Document>
    </div>
  );
};

export default ThumbNails;
