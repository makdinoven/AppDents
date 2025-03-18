import s from "./LanguageChanger.module.scss";
import LanguageIcon from "../../../common/Icons/LanguageIcon.tsx";
import ModalWrapper from "../../Modals/ModalWrapper/ModalWrapper.tsx";
import { useRef, useState } from "react";

const LanguageChanger = () => {
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);
  return (
    <>
      <button
        onClick={handleOpenModal}
        ref={triggerRef}
        className={s.language_changer}
      >
        <span className={s.language_preview}>EN</span>
        <LanguageIcon />
      </button>
      <ModalWrapper
        cutoutPosition="top-right"
        cutoutOffsetY={15}
        triggerElement={triggerRef.current}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      >
        <div>eeeeee</div>
      </ModalWrapper>
    </>
  );
};

export default LanguageChanger;
