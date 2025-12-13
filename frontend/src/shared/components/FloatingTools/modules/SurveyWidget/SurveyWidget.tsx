import s from "./SurveyWidget.module.scss";
import { Interaction } from "../../../../assets/icons";
import { Trans } from "react-i18next";
import { useSearchParams } from "react-router-dom";
import SurveyModal from "./modules/SurveyModal/SurveyModal.tsx";
import ModalOverlay from "../../../Modals/ModalOverlay/ModalOverlay.tsx";
import { useEffect, useRef, useState } from "react";
import useOutsideClick from "../../../../common/hooks/useOutsideClick.ts";
import { SurveyType } from "../../types.ts";
import { userApi } from "../../../../api/userApi/userApi.ts";
import { QuestionKey } from "./modules/SurveyModal/surveyFormType.ts";

interface InteractionWidgetProps {
  survey: SurveyType;
  onComplete: () => void;
  isScrolled: boolean;
}

const SurveyWidget = ({
  survey,
  onComplete,
  isScrolled,
}: InteractionWidgetProps) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const openSurveyParam = "_open-survey";
  const isOpen = searchParams.has(openSurveyParam);
  const closeModalRef = useRef<() => void>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const [surveyData, setSurveyData] = useState<any>();

  useEffect(() => {
    const handleFetchSurvey = async () => {
      try {
        const res = await userApi.getSurvey(survey.slug);
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
    };

    handleFetchSurvey();
  }, []);

  useEffect(() => {
    if (isOpen) {
      try {
        userApi.surveyViewed(survey.slug);
      } catch (error) {
        console.error("Survey opening error:", error);
      }
    }
  }, [isOpen, survey.slug]);

  const handleOpenSurvey = () => {
    const openSurvey = new URLSearchParams(searchParams);
    openSurvey.set(openSurveyParam, "");
    setSearchParams(openSurvey, { replace: true });
  };

  const handleModalClose = () => {
    const params = new URLSearchParams(searchParams);
    surveyData.questions
      .map((question: any) => {
        return `_q${question.id}` as QuestionKey;
      })
      .forEach((key: QuestionKey) => params.delete(key));
    params.delete(openSurveyParam);
    setSearchParams(params, { replace: true });
  };

  useOutsideClick(modalRef, () => {
    handleModalClose();
    closeModalRef.current?.();
  });

  const handleSurveyComplete = () => {
    handleModalClose();
    onComplete();
  };

  return (
    <>
      <div className={`${s.survey_widget} ${isScrolled ? s.shift : ""}`}>
        <div className={s.btn_wrapper} onClick={() => handleOpenSurvey()}>
          <button className={s.survey_btn}>
            <Interaction />
          </button>
        </div>
        <div className={s.survey_text} onClick={() => handleOpenSurvey()}>
          <span>
            <Trans i18nKey="survey.title" />
          </span>
        </div>
      </div>
      {surveyData && (
        <ModalOverlay
          isVisibleCondition={isOpen}
          modalPosition="top"
          customHandleClose={handleModalClose}
          onInitClose={(fn) => (closeModalRef.current = fn)}
        >
          <SurveyModal
            surveyData={surveyData}
            modalRef={modalRef}
            closeModal={() => closeModalRef.current?.()}
            onComplete={handleSurveyComplete}
          />
        </ModalOverlay>
      )}
    </>
  );
};
export default SurveyWidget;
