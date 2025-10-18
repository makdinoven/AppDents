import s from "../Header.module.scss";
import NavButton from "../modules/NavButton/NavButton.tsx";
import BurgerMenu from "../../ui/BurgerMenu/BurgerMenu.tsx";
import { scrollToElementById } from "../../../common/helpers/helpers.ts";
import { BooksIcon, ProfessorsIcon, QuestionMark } from "../../../assets/icons";

const PromoBookHeaderContent = () => {
  const NAV_BUTTONS_PROMOTE = [
    {
      icon: BooksIcon,
      text: "nav.promote.bookPages",
      targetId: "book-pages",
    },
    {
      icon: ProfessorsIcon,
      text: "nav.promote.bookAuthors",
      targetId: "book-authors",
    },
    { icon: QuestionMark, text: "nav.promote.faq", targetId: "book-faq" },
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
      {/*{!!oldPrice && !!newPrice && (*/}
      {/*  <button onClick={() => dispatch(openModal())} className={s.buy_btn}>*/}
      {/*    <Trans*/}
      {/*      i18nKey={"landing.buyFor"}*/}
      {/*      values={{*/}
      {/*        old_price: oldPrice,*/}
      {/*        new_price: newPrice,*/}
      {/*      }}*/}
      {/*      components={{*/}
      {/*        1: <span className="crossed-15" />,*/}
      {/*        2: <span className="highlight" />,*/}
      {/*      }}*/}
      {/*    />*/}
      {/*  </button>*/}
      {/*)}*/}
    </>
  );
};

export default PromoBookHeaderContent;
