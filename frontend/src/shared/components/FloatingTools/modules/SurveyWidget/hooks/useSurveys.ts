import { useEffect, useState } from "react";
import { SurveyType } from "../../../types.ts";
import { userApi } from "../../../../../api/userApi/userApi.ts";

export const useSurveys = (isLogged: boolean) => {
  const [surveyData, setSurveyData] = useState<any>();
  const [surveys, setSurveys] = useState<SurveyType[]>([]);
  const [currentSurveyIndex, setCurrentSurveyIndex] = useState(0);
  const currentSurvey = surveys[currentSurveyIndex];

  useEffect(() => {
    if (!isLogged) return;

    (async () => {
      try {
        const res = await userApi.getSurveys();

        const surveysResult = res.data.surveys.map(
          (survey: { slug: string; title_key: string }) => ({
            slug: survey.slug,
            titleKey: survey.title_key,
          }),
        );
        setSurveys(surveysResult);
      } catch (error) {
        console.error("Error fetching surveys", error);
      }
    })();
  }, [isLogged]);

  useEffect(() => {
    if (!isLogged || !currentSurvey?.slug) return;
    (async () => {
      try {
        const res = await userApi.getSurvey(currentSurvey.slug);
        const result = {
          slug: res.data.slug,
          titleKey: res.data.title_key,
          descriptionKey: res.data.description_key,
          questions: res.data.questions.map((q: any) => ({
            id: q.id,
            orderIndex: q.order_index,
            questionType: q.question_type,
            textKey: q.text_key,
            optionsKeys: q.options_keys,
            isRequired: q.is_required,
          })),
        };

        setSurveyData(result);
      } catch (error) {
        console.error("Survey fetching error:", error);
      }
    })();
  }, [isLogged, currentSurvey?.slug]);

  useEffect(() => {
    if (isLogged) return;

    setSurveyData(undefined);
    setSurveys([]);
    setCurrentSurveyIndex(0);
  }, [isLogged]);

  return {
    surveyData,
    setSurveyData,
    setCurrentSurveyIndex,
    currentSurvey,
  };
};
