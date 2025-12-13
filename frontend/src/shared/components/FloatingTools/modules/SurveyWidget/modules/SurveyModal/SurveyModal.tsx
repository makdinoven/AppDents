import s from "./SurveyModal.module.scss";
import { Trans } from "react-i18next";
import { t } from "i18next";
import Form from "../../../../../Modals/modules/Form/Form.tsx";
import Option from "../../../../../ui/Select/Option.tsx";
import Button from "../../../../../ui/Button/Button.tsx";
import { SendIcon } from "../../../../../../assets/icons";
import { Ref } from "react";
import { QuestionKey } from "./surveyFormType.ts";
import ModalCloseButton from "../../../../../ui/ModalCloseButton/ModalCloseButton.tsx";
import { useSurveyQuestions } from "./hooks/useSurveyQuestions.ts";
import { useSurveyForm } from "./hooks/useSurveyForm.tsx";

interface SurveyModalProps {
  surveyData: any;
  closeModal: () => void;
  modalRef: Ref<HTMLDivElement>;
  onComplete: () => void;
}

const SurveyModal = ({
  surveyData,
  closeModal,
  modalRef,
  onComplete,
}: SurveyModalProps) => {
  const { choiceQuestions, textQuestions, questionsForSchema } =
    useSurveyQuestions(surveyData);
  const {
    register,
    handleFormSubmit,
    watch,
    errors,
    textValues,
    loading,
    handleChoiceChange,
    handleInputChange,
  } = useSurveyForm({ surveyData, questionsForSchema, onComplete });

  return (
    <div className={s.survey_modal} ref={modalRef}>
      <ModalCloseButton
        className={s.close_button}
        onClick={() => closeModal()}
      />
      <Form handleSubmit={handleFormSubmit}>
        <p className={s.title}>
          <Trans i18nKey={surveyData.titleKey} />
        </p>

        <ul className={s.survey_questions}>
          <p className={s.description}>
            <Trans
              i18nKey={surveyData.descriptionKey}
              components={[<span className={s.highlight} />]}
            />
          </p>
          {choiceQuestions.length > 0 &&
            choiceQuestions.map((question: any) => {
              const key = `_q${question.id}` as QuestionKey;
              return (
                <div key={question.id} className={s.question}>
                  <p className={errors[key]?.message ? s.error : ""}>
                    {(errors[key]?.message && t(errors[key]?.message)) ||
                      `${question.id}. ${t(question.textKey)}${question.isRequired ? " *" : ""}`}
                  </p>
                  {question.optionsKeys &&
                    question.optionsKeys.length > 0 &&
                    question.optionsKeys
                      .map((option: string, index: number) => ({
                        value: String(index + 1),
                        label: t(option),
                      }))
                      .map((option: { value: string; label: string }) => {
                        const fieldValue = watch(key) as string | undefined;
                        const isMultiple =
                          question.questionType === "MULTIPLE_CHOICE";

                        const isActive = isMultiple
                          ? fieldValue?.split(",").includes(option.value)
                          : fieldValue === option.value;
                        return (
                          <Option
                            key={option.value}
                            option={option}
                            onChange={(val) =>
                              handleChoiceChange(
                                question,
                                key,
                                option.value,
                                val,
                              )
                            }
                            className={s.option}
                            radioButtonType={isMultiple ? "checkbox" : "radio"}
                            isActive={isActive}
                            activeClassName={s.active}
                            allowUncheck={isMultiple}
                          />
                        );
                      })}
                </div>
              );
            })}
          <div className={s.bottom_els}>
            {textQuestions.length > 0 &&
              textQuestions.map((question: any) => {
                const key = `_q${question.id}` as QuestionKey;
                return (
                  <div key={question.id} className={s.question}>
                    <label
                      htmlFor={key}
                      className={errors[key]?.message ? s.error : ""}
                    >
                      {(errors[key]?.message && t(errors[key]?.message)) ||
                        `${question.id}. ${t(question.textKey)}`}
                    </label>
                    <textarea
                      id={key}
                      className={s.comment_input}
                      placeholder={t("typeHere")}
                      {...register(key)}
                      onChange={(e) => handleInputChange(key, e)}
                      value={textValues[key]}
                    />
                  </div>
                );
              })}

            <Button
              type="submit"
              variant="filled"
              text="send"
              className={s.submit_btn}
              iconLeft={<SendIcon />}
              loading={loading}
            />
          </div>
        </ul>
      </Form>
    </div>
  );
};

export default SurveyModal;
