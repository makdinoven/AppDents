import s from "./ProfessorBuySection.module.scss";
import {
  PaymentDataModeType,
  usePaymentPageHandler,
} from "../../../../shared/common/hooks/usePaymentPageHandler.ts";
import BuySectionIcons from "../BuySectionIcons/BuySectionIcons.tsx";
import { t } from "i18next";
import { Trans } from "react-i18next";
import { getDiscountPercent } from "../../../../shared/common/helpers/helpers.ts";
import { useSelector } from "react-redux";

const ProfessorBuySection = ({
  setPaymentDataCustom,
  prices,
}: {
  setPaymentDataCustom: (mode: PaymentDataModeType) => void;
  prices: {
    books: { old: number; new: number };
    courses: { old: number; new: number };
    both: { old: number; new: number };
  };
}) => {
  const language = useSelector((state: any) => state.user.language);
  const { openPaymentModal } = usePaymentPageHandler();

  const handleOpenModal = (paymentDataMode: PaymentDataModeType) => {
    setPaymentDataCustom(paymentDataMode);
    openPaymentModal(undefined, undefined, paymentDataMode);
  };

  const buyOptions: {
    mode: PaymentDataModeType;
    btn_label: string;
    className: string;
    prices: { old: number; new: number };
    label: string;
    benefits: { name: string }[];
  }[] = [
    {
      mode: "COURSES",
      label: "professor.allCourses",
      btn_label: `${t("get")}`,
      className: s.courses,
      prices: { old: prices.courses.old, new: prices.courses.new },
      benefits: [
        { name: `4 courses` },
        { name: `unlimited access` },
        { name: `extra discount` },
      ],
    },
    {
      mode: "BOTH",
      label: "professor.allCoursesAndBooks",
      btn_label: `${t("get")}`,
      className: s.both,
      prices: { old: prices.both.old, new: prices.both.new },
      benefits: [
        { name: `4 courses` },
        { name: `4 books` },
        { name: `unlimited access` },
        { name: `extra discount` },
      ],
    },
    {
      mode: "BOOKS",
      label: "professor.allBooks",
      btn_label: `${t("get")}`,
      className: s.books,
      prices: { old: prices.books.old, new: prices.books.new },
      benefits: [
        { name: `4 books` },
        { name: `unlimited access` },
        { name: `extra discount` },
      ],
    },
  ];

  const openModal = (mode: PaymentDataModeType) => {
    handleOpenModal(mode);
  };

  return (
    <div className={s.buy_section}>
      {buyOptions.map(({ mode, btn_label, className, prices, label }) => (
        <div
          key={mode}
          onClick={() => openModal(mode)}
          className={`${s.buy_variant} ${className}`}
        >
          <BuySectionIcons paymentMode={mode} />

          <div className={s.top_section}>
            <h4 className={s.section_name}>
              <Trans i18nKey={label} />
            </h4>
            <div className={s.prices}>
              <span className={s.new}>${prices.new}</span>
              <span className={s.old}>${prices.old}</span>
            </div>
          </div>

          <p lang={language.toLowerCase()} className={s.info}>
            <Trans
              i18nKey={`professor.youCanBuyAll.${mode.toLowerCase()}`}
              values={{
                new_price: prices.new,
                old_price: prices.old,
              }}
              components={{
                1: <span className={s.new_price} />,
                2: <span className={s.old_price} />,
              }}
            />
          </p>

          <div className={s.bottom_section}>
            {/*<ul className={s.benefits_list}>*/}
            {/*  {benefits.map((benefit, i) => (*/}
            {/*    <li key={i}>*/}
            {/*      <span> – {benefit.name}</span>*/}
            {/*    </li>*/}
            {/*  ))}*/}
            {/*</ul>*/}

            <button className={s.buy_btn} onClick={() => openModal(mode)}>
              {btn_label}
            </button>
            <div className={s.savings}>
              {getDiscountPercent(prices.old, prices.new)}%{" "}
              <Trans i18nKey={"landing.savings"} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ProfessorBuySection;
