export type SurveyType = {
  slug: string;
  titleKey: string;
};

export type AnswerType = {
  question_id: number;
  answer_choice: number[];
  answer_text: string;
};

export type QuestionType = "SINGLE_CHOICE" | "MULTIPLE_CHOICE" | "FREE_TEXT";
