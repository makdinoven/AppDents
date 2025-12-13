import { useSearchParams } from "react-router-dom";
import { ChangeEvent, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import {
  QuestionKey,
  SurveyFormType,
  SurveyQuestionType,
} from "../surveyFormType.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { surveySchema } from "../surveySchema.ts";
import { userApi } from "../../../../../../../api/userApi/userApi.ts";
import { Alert } from "../../../../../../ui/Alert/Alert.tsx";
import { t } from "i18next";
import { CheckMark } from "../../../../../../../assets/icons";
import { AnswerType } from "../../../../../types.ts";

interface UseSurveyFormParams {
  surveyData: any;
  questionsForSchema: SurveyQuestionType[];
  onComplete: () => void;
}

export const useSurveyForm = ({
  surveyData,
  questionsForSchema,
  onComplete,
}: UseSurveyFormParams) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [textValues, setTextValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const restored: Record<string, string> = {};

    surveyData.questions
      .filter((q: any) => q.questionType === "FREE_TEXT")
      .forEach((q: any) => {
        const key = `_q${q.id}`;
        const value = searchParams.get(key);
        if (value !== null) restored[key] = value;
      });

    setTextValues(restored);
  }, [searchParams, surveyData]);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
    formState,
  } = useForm<SurveyFormType>({
    resolver: joiResolver(surveySchema(questionsForSchema)),
    defaultValues: surveyData.questions.reduce(
      (full: SurveyFormType, q: any) => {
        const key = `_q${q.id}` as QuestionKey;
        full[key] = searchParams.get(key) ?? "";
        return full;
      },
      {} as SurveyFormType,
    ),
    mode: "onSubmit",
  });

  const handleChoiceChange = (
    question: any,
    key: QuestionKey,
    optionValue: string,
    _rawValue?: string,
  ) => {
    const isMultiple = question.questionType === "MULTIPLE_CHOICE";
    const params = new URLSearchParams(searchParams);

    const current = (params.get(key) ?? watch(key) ?? "") as string;

    if (!isMultiple) {
      params.set(key, optionValue);
      setSearchParams(params, { replace: true });
      setValue(key, optionValue, { shouldValidate: true });
      return;
    }

    const parts = current ? current.split(",").filter(Boolean) : [];
    const set = new Set(parts);

    if (set.has(optionValue)) {
      set.delete(optionValue);
    } else {
      set.add(optionValue);
    }

    const result = Array.from(set);
    const joined = result.join(",");

    if (joined) {
      params.set(key, joined);
    } else {
      params.delete(key);
    }

    setSearchParams(params, { replace: true });
    setValue(key, joined, {
      shouldValidate: formState.isSubmitted,
      shouldDirty: true,
    });
  };

  const handleInputChange = (
    param: keyof SurveyFormType,
    e: ChangeEvent<HTMLTextAreaElement>,
  ) => {
    const value = e.target.value;
    setTextValues((prev: Record<string, string>) => ({
      ...prev,
      [param]: value,
    }));

    const params = new URLSearchParams(searchParams);

    if (value) {
      params.set(param, value);
    } else {
      params.delete(param);
    }

    setSearchParams(params, { replace: true });
    setValue(param, value, {
      shouldValidate: formState.isSubmitted,
      shouldDirty: true,
    });
  };

  const handleSendSurveyAnswers = async (formValues: SurveyFormType) => {
    const answers = surveyData.questions.reduce(
      (acc: AnswerType[], question: any) => {
        const key = `_q${question.id}` as QuestionKey;
        const rawValue = formValues[key];

        if (!rawValue) return acc;

        if (question.questionType === "FREE_TEXT") {
          acc.push({
            question_id: question.id,
            answer_choice: [],
            answer_text: rawValue,
          });
          return acc;
        }

        const parts = rawValue.split(",").filter(Boolean);
        const nums = parts.map(Number);

        acc.push({
          question_id: question.id,
          answer_choice: nums,
          answer_text: "",
        });

        return acc;
      },
      [],
    );

    const body = { answers };

    try {
      setLoading(true);
      const res = await userApi.submitSurvey(surveyData.slug, body);
      if (res.data.status === "ok") {
        onComplete();
        Alert(t(res.data.message_key), <CheckMark />);
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleFormSubmit = handleSubmit(handleSendSurveyAnswers);

  return {
    register,
    handleFormSubmit,
    setValue,
    watch,
    errors,
    textValues,
    loading,
    handleChoiceChange,
    handleInputChange,
  };
};
