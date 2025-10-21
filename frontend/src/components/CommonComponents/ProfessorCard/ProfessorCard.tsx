import s from "./ProfessorCard.module.scss";
import ViewLink from "../../ui/ViewLink/ViewLink.tsx";
import { Link } from "react-router-dom";
import INITIAL_PHOTO from "../../../assets/no-pictures.png";
import { Trans } from "react-i18next";
import { t } from "i18next";
import React from "react";

const ProfessorCard = ({
  variant,
  name,
  photo,
  description,
  tags,
  courses_count,
  books_count,
  link,
}: {
  variant: "vertical" | "horizontal";
  name: string;
  photo: string;
  courses_count: number;
  books_count: number;
  tags: string[];
  description: string;
  link: string;
}) => {
  return (
    <Link to={link} className={s.card_wrapper}>
      <div className={s.card_header}>
        <h6>{name}</h6>
      </div>
      <div className={s.professor_card}>
        <div
          style={{
            flexDirection: `${variant === "horizontal" ? "row" : "column"}`,
          }}
          className={s.card_content}
        >
          <div className={s.photo_wrapper}>
            <img src={photo ? photo : INITIAL_PHOTO} alt="professor photo" />
          </div>
          <div className={s.description_wrapper}>
            {courses_count > 0 && books_count > 0 && (
              <div className={s.counts}>
                {courses_count > 0 && (
                  <span
                    style={{
                      alignSelf: `${variant === "horizontal" ? "flex-start" : "center"}`,
                    }}
                    className={s.courses_count}
                  >
                    <Trans
                      i18nKey="professor.coursesCount"
                      count={courses_count}
                    />
                  </span>
                )}

                {books_count > 0 && (
                  <span
                    style={{
                      alignSelf: `${variant === "horizontal" ? "flex-start" : "center"}`,
                    }}
                    className={s.books_count}
                  >
                    <Trans i18nKey="professor.booksCount" count={books_count} />
                  </span>
                )}
              </div>
            )}

            <p className={s.description}>{description}</p>
            {tags.length > 0 && (
              <span className={s.tags}>
                <span className={"highlight"}>
                  <Trans i18nKey={"professor.specialization"} />
                </span>{" "}
                {tags.map((tag, index) => (
                  <React.Fragment key={tag}>
                    {t(tag)}
                    {index !== tags.length - 1 && ", "}
                  </React.Fragment>
                ))}
              </span>
            )}
          </div>
          <ViewLink className={s.professor_link} text={"professor.about"} />
        </div>
      </div>
    </Link>
  );
};

export default ProfessorCard;
