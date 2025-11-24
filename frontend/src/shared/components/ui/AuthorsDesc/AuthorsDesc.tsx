import s from "./AuthorsDesc.module.scss";
import FormattedAuthorsDesc from "../../../common/helpers/FormattedAuthorsDesc.tsx";

const AuthorsDesc = ({
  authors,
  size,
  color,
  flexWrap = false,
}: {
  authors: any[];
  color?: any;
  size?: "small" | "large";
  flexWrap?: boolean;
}) => {
  const visibleAuthors = authors?.slice(0, 3).filter((author) => author.photo);

  return (
    <div
      style={{ flexWrap: flexWrap ? "wrap" : "nowrap" }}
      className={`${s.course_authors} ${size ? s[size] : ""}`}
    >
      {visibleAuthors?.length > 0 && (
        <ul className={s.authors_photos_list}>
          {visibleAuthors?.map((author) => (
            <li
              key={author.id}
              style={{ backgroundImage: `url("${author.photo}")` }}
              className={`${s.author_photo} ${color ? s[color] : ""}`}
            ></li>
          ))}
        </ul>
      )}
      <p>
        <FormattedAuthorsDesc authors={authors} />
      </p>
    </div>
  );
};

export default AuthorsDesc;
