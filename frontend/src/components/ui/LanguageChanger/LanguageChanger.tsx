import s from "./LanguageChanger.module.scss";
import LanguageIcon from "../../../common/Icons/LanguageIcon.tsx";
import ModalWrapper from "../../Modals/ModalWrapper/ModalWrapper.tsx";
import { useRef, useState } from "react";
import CheckMark from "../../../common/Icons/CheckMark.tsx";
import { languages } from "../../../common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType } from "../../../store/store.ts";
import { setLanguage } from "../../../store/slices/userSlice.ts";

const LanguageChanger = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const language = useSelector((state: any) => state.user.language);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  const handleLanguageChange = (selectedLanguage: string) => {
    dispatch(setLanguage(selectedLanguage));
    handleCloseModal();
  };

  return (
    <>
      <button
        onClick={handleOpenModal}
        ref={triggerRef}
        className={s.language_changer}
      >
        <span className={s.language_preview}>{language.toUpperCase()}</span>
        <LanguageIcon />
      </button>
      <ModalWrapper
        isLang={true}
        hasTitle={false}
        hasCloseButton={false}
        cutoutPosition="top-right"
        cutoutOffsetY={10}
        cutoutOffsetX={15}
        triggerElement={triggerRef.current}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      >
        <ul className={s.language_changer_modal}>
          {languages.map((button) => (
            <li
              key={button.value}
              onClick={() => handleLanguageChange(button.value)}
            >
              ({button.value}) {button.label}
              {button.value === language.toUpperCase() && <CheckMark />}
            </li>
          ))}
        </ul>
      </ModalWrapper>
    </>
  );
};

export default LanguageChanger;
