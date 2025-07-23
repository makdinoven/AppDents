import s from "../Header.module.scss";
import NavButton from "../modules/NavButton/NavButton.tsx";
import BurgerMenu from "../../ui/BurgerMenu/BurgerMenu.tsx";
import { openModal } from "../../../store/slices/landingSlice.ts";
import { Trans } from "react-i18next";
import {
  BooksIcon,
  ProfessorsIcon,
  QuestionMark,
} from "../../../assets/icons/index";
import {
  getBasePath,
  scrollToElementById,
} from "../../../common/helpers/helpers.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { Path } from "../../../routes/routes.ts";
import { useLocation } from "react-router-dom";
import { openPaymentModal } from "../../../store/slices/paymentSlice.ts";

const PromoHeaderContent = () => {
  const location = useLocation();
  const dispatch = useDispatch<AppDispatchType>();
  const oldPrice = useSelector(
    (state: AppRootStateType) => state.payment.data?.oldPrice,
  );
  const newPrice = useSelector(
    (state: AppRootStateType) => state.payment.data?.newPrice,
  );
  const basePath = getBasePath(location.pathname);
  const isWebinar = basePath === Path.webinarLanding;

  const NAV_BUTTONS_PROMOTE = [
    {
      icon: BooksIcon,
      text: `${isWebinar ? "nav.promote.webinarProgram" : "nav.promote.program"}`,
      targetId: `${isWebinar ? "webinar-program" : "course-program"}`,
    },
    {
      icon: ProfessorsIcon,
      text: `${isWebinar ? "nav.promote.webinarProfessors" : "nav.promote.professors"}`,
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
        <button
          onClick={() => dispatch(openPaymentModal())}
          className={s.buy_btn}
        >
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
