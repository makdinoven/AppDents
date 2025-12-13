import s from "./SurveyWidget.module.scss";
import { Interaction } from "../../../../assets/icons";
import { Trans } from "react-i18next";
import SurveyModal from "./modules/SurveyModal/SurveyModal.tsx";
import ModalOverlay from "../../../Modals/ModalOverlay/ModalOverlay.tsx";
import { useEffect, useMemo, useRef } from "react";
import useOutsideClick from "../../../../common/hooks/useOutsideClick.ts";
import { userApi } from "../../../../api/userApi/userApi.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../store/store.ts";
import { useSurveys } from "./hooks/useSurveys.ts";
import { useSurveyParam } from "./hooks/useSurveyParam.ts";

interface InteractionWidgetProps {
  callback: (showSurvey: boolean) => void;
  isScrolled: boolean;
}

const SurveyWidget = ({ callback, isScrolled }: InteractionWidgetProps) => {
  const closeModalRef = useRef<() => void>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const { isLogged } = useSelector((state: AppRootStateType) => state.user);

  const { surveyData, setSurveyData, setCurrentSurveyIndex, currentSurvey } =
    useSurveys(isLogged);
  const { isOpen, handleOpenSurvey, handleModalClose } = useSurveyParam({
    surveyData,
    currentSurvey,
  });

  const showSurvey = useMemo(
    () => Boolean(isLogged && currentSurvey),
    [isLogged, currentSurvey],
  );

  useEffect(() => {
    callback(showSurvey);
  }, [callback, showSurvey]);

  useEffect(() => {
    if (!isOpen || !currentSurvey?.slug) return;

    (async () => {
      try {
        await userApi.surveyViewed(currentSurvey?.slug);
      } catch (error) {
        console.error("Survey opening error:", error);
      }
    })();
  }, [isOpen, currentSurvey?.slug]);

  useOutsideClick(modalRef, () => {
    if (!isOpen) return;
    handleModalClose();
    closeModalRef.current?.();
  });

  const handleSurveyComplete = () => {
    handleModalClose();
    setCurrentSurveyIndex((prev) => prev + 1);
    setSurveyData(undefined);
  };

  return isLogged && currentSurvey ? (
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
  ) : null;
};
export default SurveyWidget;
