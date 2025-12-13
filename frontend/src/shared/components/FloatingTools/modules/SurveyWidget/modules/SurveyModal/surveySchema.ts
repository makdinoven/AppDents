import Joi from "joi";
import { SurveyFormType, SurveyQuestionType } from "./surveyFormType.ts";

export const surveySchema = (questions: SurveyQuestionType[]) => {
  const shape: Record<string, Joi.StringSchema> = {};

  questions.forEach((q) => {
    const key = `_q${q.id}`;

    let field = Joi.string().empty("");

    if (q.type === "FREE_TEXT") {
      field = field.min(10).max(1000).messages({
        "string.min": "error.survey.min",
        "string.max": "error.survey.max",
      });
    }

    if (q.required) {
      field = field.required().messages({
        "any.required": "error.survey.required",
      });
    } else {
      field = field.optional();
    }

    shape[key] = field;
  });

  return Joi.object<SurveyFormType>(shape);
};
