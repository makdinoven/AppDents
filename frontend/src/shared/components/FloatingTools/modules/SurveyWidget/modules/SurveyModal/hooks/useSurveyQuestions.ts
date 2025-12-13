import { SurveyQuestionType } from "../surveyFormType.ts";

export const useSurveyQuestions = (surveyData: any) => {
  const choiceQuestions = surveyData.questions.filter(
    (question: any) => question.questionType !== "FREE_TEXT",
  );

  const textQuestions = surveyData.questions.filter(
    (question: any) => question.questionType === "FREE_TEXT",
  );

  const questionsForSchema: SurveyQuestionType[] = surveyData.questions.map(
    (question: any) => ({
      id: question.id,
      type: question.questionType,
      required: question.isRequired,
    }),
  );

  return { choiceQuestions, textQuestions, questionsForSchema };
};
