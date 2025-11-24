import React, { useState } from "react";
import { Thumbnail } from "react-pdf";
import s from "./ThumbNails.module.scss";

interface IThumbNailsProps {
  isOpen: boolean;
  totalPages: number | undefined;
  handlePageChange: (currentPage: number) => void;
  currentPage: number;
}

const ThumbNails = ({
  isOpen,
  totalPages,
  handlePageChange,
  currentPage,
}: IThumbNailsProps) => {
  const [activeThumbNail, setActiveThumbNail] = useState(currentPage);

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
  };

  const handleThumbNailClick = (currentPage: number) => {
    handlePageChange(currentPage);
    setActiveThumbNail(currentPage);
  };

  const handleThumbNailsAreaClick = (
    event: React.MouseEvent<HTMLDivElement>,
  ) => {
    event.stopPropagation();
  };

  return (
    <div
      className={`${s.thumb_nails_wrapper} ${isOpen && s.open}`}
      onContextMenu={handleContextMenu}
      onClick={handleThumbNailsAreaClick}
    >
      <ul className={s.thumb_nails_list}>
        {totalPages &&
          Array.from({ length: totalPages as number }, (_, i) => {
            const currentPage = i + 1;
            return (
              <li
                key={currentPage}
                className={`${s.thumb_nail_wrapper} ${activeThumbNail === currentPage && s.active}`}
              >
                <Thumbnail
                  pageNumber={currentPage}
                  width={100}
                  canvasBackground="white"
                  className={s.thumb_nail}
                  onClick={() => handleThumbNailClick(currentPage)}
                  renderMode="canvas"
                  loading="lazy"
                />
                <span className={s.page}>{currentPage}</span>
              </li>
            );
          })}
      </ul>
    </div>
  );
};

export default ThumbNails;
