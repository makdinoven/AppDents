import s from "./UniversalPage.module.scss";
import { useParams } from "react-router-dom";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import { useTranslation } from "react-i18next";
import { useEffect, useState } from "react";
import { mainApi } from "../../api/mainApi/mainApi.ts";

const UniversalPage = () => {
  const { pageType } = useParams();
  const { i18n } = useTranslation();
  const language = i18n.language.toLowerCase();
  const [content, setContent] = useState<string>("");

  const pageInfo: Record<string, { title: string; content: string }> = {
    "terms-of-use": {
      title: "footer.terms",
      content,
    },
    "privacy-policy": {
      title: "footer.privacy",
      content,
    },
    "cookie-policy": {
      title: "footer.cookie",
      content,
    },
  };

  useEffect(() => {
    if (!pageType || !language) return;
    mainApi
      .getPageInfo(pageType, language)
      .then((res) => {
        if (res.data) {
          setContent(res.data.content || "");
        }
      })
      .catch((error) => {
        console.log(error);
      });
  }, [language, pageType]);

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
