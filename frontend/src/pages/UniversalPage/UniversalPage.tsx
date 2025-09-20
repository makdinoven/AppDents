import s from "./UniversalPage.module.scss";
import { useParams } from "react-router-dom";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import Loader from "../../components/ui/Loader/Loader.tsx";
import { t } from "i18next";

const UniversalPage = () => {
  const { pageType } = useParams();
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const [loading, setLoading] = useState(true);
  const [content, setContent] = useState<string[] | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const pageInfo: Record<
    string,
    {
      title: string;
      api: () => Promise<{ data: { content: string } }>;
    }
  > = {
    "terms-of-use": {
      title: "footer.terms",
      api: () => mainApi.getTermsOfUse(language),
    },
    "privacy-policy": {
      title: "footer.privacy",
      api: () => mainApi.getPrivacyPolicy(language),
    },
    "cookie-policy": {
      title: "footer.cookie",
      api: () => mainApi.getCookiePolicy(language),
    },
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const res = await page.api();
      setContent(splitBySentences(res.data.content));
    } catch (e) {
      setLoading(false);
      setError(t("nothingFound"));
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const page = pageInfo[pageType || ""] || { title: "", api: "" };

  return (
    <>
      <div className={s.page_container}>
        <DetailHeader title={page.title} />
        {!content && loading && !error ? (
          <Loader />
        ) : (
          content && (
            <div className={s.page_content}>
              {content.map((p, idx) => (
                <p key={idx}>{p}</p>
              ))}
            </div>
          )
        )}

        {error && error}
      </div>
    </>
  );
};

export default UniversalPage;
