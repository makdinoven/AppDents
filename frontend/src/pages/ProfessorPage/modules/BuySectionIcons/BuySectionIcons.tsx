import s from "./BuySectionIcons.module.scss";
import { BooksIcon, CoursesIcon } from "../../../../shared/assets/icons";
import { PaymentDataModeType } from "../../../../shared/common/hooks/usePaymentPageHandler.ts";

const BuySectionIcons = ({
  paymentMode,
}: {
  paymentMode: PaymentDataModeType;
}) => {
  const modeIcons = {
    COURSES: [<CoursesIcon />],
    BOOKS: [<BooksIcon />],
    BOTH: [<CoursesIcon />, <BooksIcon />],
  };

  return (
    <div className={`${s.icons} ${s[paymentMode.toLowerCase()]}`}>
      {modeIcons[paymentMode].map((icon, i) => (
        <div key={i} className={`${s.icon} ${s[paymentMode.toLowerCase()]}`}>
          {icon}
        </div>
      ))}
    </div>
  );
};

export default BuySectionIcons;
