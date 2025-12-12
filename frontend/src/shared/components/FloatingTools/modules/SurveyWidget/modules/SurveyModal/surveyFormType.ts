import { QuestionType } from "../../../../types.ts";

export type QuestionKey = `q${number}`;

export type SurveyFormType = {
  [key: QuestionKey]: string;
};

export type SurveyQuestionType = {
  id: number;
  type: QuestionType;
  required: boolean;
};
