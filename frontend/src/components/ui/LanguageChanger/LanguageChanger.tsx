import s from "./LanguageChanger.module.scss";
import { useRef, useState } from "react";
import { LANGUAGES } from "../../../common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType } from "../../../store/store.ts";
import { setLanguage } from "../../../store/slices/userSlice.ts";
import LangLogo, { LanguagesType } from "../LangLogo/LangLogo.tsx";
import useOutsideClick from "../../../common/hooks/useOutsideClick.ts";

const LanguageChanger = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const language = useSelector((state: any) => state.user.language);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const modalRef = useRef<HTMLDivElement | null>(null);
  const handleOpenModal = () => setIsModalOpen(true);
  const [isClosing, setIsClosing] = useState(false);

  const handleCloseModal = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      setIsModalOpen(false);
    }, 200);
  };
  useOutsideClick(modalRef, handleCloseModal);

  const handleLanguageChange = (selectedLanguage: string) => {
    dispatch(setLanguage(selectedLanguage));
    handleCloseModal();
  };

  return (
    <div className={s.language_changer_container}>
      <button
        onClick={handleOpenModal}
        ref={triggerRef}
        className={s.language_changer}
      >
        <LangLogo
          isHoverable
          className={s.lang_logo}
          isChecked={isModalOpen}
          lang={language}
        />
      </button>
      {isModalOpen && (
        <div
          ref={modalRef}
          className={`${s.language_changer_modal} ${isClosing ? s.closing : ""}`}
        >
          {LANGUAGES.filter(
            (button) => button.value !== language.toUpperCase(),
          ).map((button) => (
            <LangLogo
              key={button.value}
              isChecked={button.value === language.toUpperCase()}
              lang={button.value as LanguagesType}
              isHoverable
              onClick={() => handleLanguageChange(button.value)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default LanguageChanger;
