import s from "./SimpleBuySection.module.scss";
import {
  PaymentDataModeType,
  usePaymentPageHandler,
} from "../../../../common/hooks/usePaymentPageHandler.ts";
import { Trans } from "react-i18next";
import ArrowButton from "../../../../components/ui/ArrowButton/ArrowButton.tsx";
import BuySectionIcons from "../BuySectionIcons/BuySectionIcons.tsx";

const SimpleBuySection = ({
  paymentMode,
  setPaymentDataCustom,
  new_price,
  old_price,
}: {
  paymentMode: PaymentDataModeType;
  setPaymentDataCustom: (paymentDataMode: PaymentDataModeType) => void;
  new_price: number;
  old_price: number;
}) => {
  const { openPaymentModal } = usePaymentPageHandler();

  const handleOpenModal = (paymentDataMode: PaymentDataModeType) => {
    setPaymentDataCustom(paymentDataMode);
    openPaymentModal(undefined, undefined, paymentDataMode);
  };

  return (
    <section
      onClick={() => handleOpenModal(paymentMode)}
      className={`${s.buy_section} ${s[paymentMode.toLowerCase()]}`}
    >
      {/*<Clock className={s.clock_icon} />*/}
      <BuySectionIcons paymentMode={paymentMode} />
      <p className={s.professor_access}>
        <Trans i18nKey={`professor.accessToAll.${paymentMode.toLowerCase()}`} />
      </p>
      <p className={s.buy_section_desc}>
        <Trans
          i18nKey={`professor.youCanBuyAll.${paymentMode.toLowerCase()}`}
          values={{
            new_price: new_price,
            old_price: old_price,
          }}
          components={{
            1: <span className={s.new_price} />,
            2: <span className="crossed" />,
          }}
        />
      </p>
      <ArrowButton>
        <Trans
          i18nKey={`professor.getAll.${paymentMode.toLowerCase()}`}
          values={{
            new_price: new_price,
          }}
          components={{
            1: <span className={s.new_price} />,
          }}
        />
      </ArrowButton>
    </section>
  );
};

export default SimpleBuySection;
