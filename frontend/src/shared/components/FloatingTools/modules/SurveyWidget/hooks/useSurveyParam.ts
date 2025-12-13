import { useSearchParams } from "react-router-dom";
import { QuestionKey } from "../modules/SurveyModal/surveyFormType.ts";
import { SurveyType } from "../../../types.ts";
interface UseSurveyParamParams {
  surveyData: any;
  currentSurvey: SurveyType;
}
export const useSurveyParam = ({
  surveyData,
  currentSurvey,
}: UseSurveyParamParams) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const openSurveyParam = "_open-survey";
  const isOpen = !!searchParams.get(openSurveyParam);

  const handleOpenSurvey = () => {
    if (!currentSurvey?.slug) return;
    const openSurvey = new URLSearchParams(searchParams);
    openSurvey.set(openSurveyParam, currentSurvey?.slug);
    setSearchParams(openSurvey, { replace: true });
  };

  const handleModalClose = () => {
    const params = new URLSearchParams(searchParams);
    const questions = surveyData?.questions ?? [];

    questions
      .map((question: any) => {
        return `_q${question.id}` as QuestionKey;
      })
      .forEach((key: QuestionKey) => params.delete(key));
    params.delete(openSurveyParam);
    setSearchParams(params, { replace: true });
  };

  return {
    isOpen,
    handleOpenSurvey,
    handleModalClose,
  };
};
