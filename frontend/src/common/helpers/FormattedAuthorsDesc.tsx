import { capitalizeText } from "./helpers.ts";
import { t } from "i18next";
import { useNavigate } from "react-router-dom";
import { Path } from "../../routes/routes.ts";

const FormattedAuthorsDesc = ({ authors }: any) => {
  const navigate = useNavigate();
  if (!authors?.length) return null;

  const displayedAuthors = authors
    .slice(0, 3)
    .map((author: any, index: number) => (
      <span onClick={(e) => e.preventDefault()} key={author.id}>
        <span
          style={{ textDecoration: "underline", cursor: "pointer" }}
          onClick={() => navigate(`${Path.professor}/${author.id}`)}
        >
          {capitalizeText(author.name)}
        </span>
        {index < authors.length - 1 && ", "}
      </span>
    ));

  return (
    <>
      {t("landing.by")} {displayedAuthors}
      {authors.length > 3 && ` ${t("etAl")}`}
    </>
  );
};

export default FormattedAuthorsDesc;
