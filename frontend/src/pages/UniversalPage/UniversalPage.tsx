import s from "./UniversalPage.module.scss";
import { useParams } from "react-router-dom";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import { t } from "i18next";

const UniversalPage = () => {
  const { pageType } = useParams();

  const pageInfo: Record<string, { title: string; content: string }> = {
    "terms-of-use": {
      title: "footer.terms",
      content: t("footer.terms.content"),
    },
    "privacy-policy": {
      title: "footer.privacy",
      content: t("footer.privacy.content"),
    },
    "cookie-policy": {
      title: "footer.cookie",
      content: t("footer.cookie.content"),
    },
  };

  const page = pageInfo[pageType || ""] || { title: "", content: "" };
  const splitBySentences = (text: string) => {
    return text.split(/(?<=[.!?])\s+/).reduce((acc, sentence) => {
      if (!acc.length) {
        acc.push(sentence);
      } else {
        if (acc[acc.length - 1].length + sentence.length < 400) {
          acc[acc.length - 1] += " " + sentence;
        } else {
          acc.push(sentence);
        }
      }
      return acc;
    }, [] as string[]);
  };

  const paragraphs = splitBySentences(page.content);

  return (
    <>
      <div className={s.page_container}>
        <DetailHeader title={page.title} />
        <div className={s.page_content}>
          {paragraphs.map((p, idx) => (
            <p key={idx}>{p}</p>
          ))}
        </div>
      </div>
    </>
  );
};

export default UniversalPage;
