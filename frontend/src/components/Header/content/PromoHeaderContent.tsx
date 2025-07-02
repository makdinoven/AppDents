import s from "../Header.module.scss";
import NavButton from "../modules/NavButton/NavButton.tsx";
import BurgerMenu from "../../ui/BurgerMenu/BurgerMenu.tsx";
import { openModal } from "../../../store/slices/landingSlice.ts";
import { Trans } from "react-i18next";
import { BooksIcon, ProfessorsIcon, QuestionMark } from "../../../assets/icons";
import { scrollToElementById } from "../../../common/helpers/helpers.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";

const PromoHeaderContent = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const oldPrice = useSelector(
    (state: AppRootStateType) => state.landing.oldPrice
  );
  const newPrice = useSelector(
    (state: AppRootStateType) => state.landing.newPrice
  );

  const NAV_BUTTONS_PROMOTE = [
    {
      icon: BooksIcon,
      text: "nav.promote.program",
      targetId: "course-program",
    },
    {
      icon: ProfessorsIcon,
      text: "nav.promote.professors",
      targetId: "course-professors",
    },
    { icon: QuestionMark, text: "nav.promote.faq", targetId: "course-faq" },
  ].map((button) => ({
    ...button,
    onClick: () => scrollToElementById(button.targetId),
  }));

  return (
    <>
      <div className={s.nav_center}>
        {NAV_BUTTONS_PROMOTE.map((btn) => (
          <NavButton
            key={btn.text}
            icon={btn.icon}
            text={btn.text}
            onClick={btn.onClick}
          />
        ))}
      </div>
      <BurgerMenu buttons={NAV_BUTTONS_PROMOTE} />
      {!!oldPrice && !!newPrice && (
        <button onClick={() => dispatch(openModal())} className={s.buy_btn}>
          <Trans
            i18nKey={"landing.buyFor"}
            values={{
              old_price: oldPrice,
              new_price: newPrice,
            }}
            components={{
              1: <span className="crossed-15" />,
              2: <span className="highlight" />,
            }}
          />
        </button>
      )}
    </>
  );
};

export default PromoHeaderContent;
