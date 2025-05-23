import ModalWrapper from "../../Modals/ModalWrapper/ModalWrapper.tsx";
import s from "./BurgerMenu.module.scss";
import { useRef, useState } from "react";
import NavButton from "../../Header/modules/NavButton/NavButton.tsx";

const BurgerMenu = ({ buttons }: { buttons: any[] }) => {
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleOpenModal = () => setIsModalOpen(true);
  const handleCloseModal = () => setIsModalOpen(false);

  return (
    <>
      <button
        onClick={handleOpenModal}
        ref={triggerRef}
        className={`${s.burger_btn} ${isModalOpen ? s.active : ""}`}
      >
        <span></span>
        <span></span>
        <span></span>
      </button>
      {isModalOpen && (
        <ModalWrapper
          isDropdown={true}
          hasTitle={false}
          hasCloseButton={false}
          cutoutPosition="top-left"
          cutoutOffsetY={10}
          cutoutOffsetX={15}
          triggerElement={triggerRef.current}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
        >
          <div className={s.burger_menu_content}>
            {buttons.map((btn) => (
              <NavButton
                appearance={"light"}
                key={btn.text}
                icon={btn.icon}
                text={btn.text}
                link={btn.link}
                onClick={() => {
                  btn.onClick();
                  handleCloseModal();
                }}
                isActive={location.pathname === btn.link}
              />
            ))}
          </div>
        </ModalWrapper>
      )}
    </>
  );
};

export default BurgerMenu;
