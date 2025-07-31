import s from "./LogoList.module.scss";
import {
  AmexLogo,
  ApplePayLogo,
  DinnerClubLogo,
  DiscoverLogo,
  GooglePayLogo,
  JcbLogo,
  MastercardLogo,
  PaypalLogo,
  UnionPayLogo,
  VisaLogo,
} from "../../../../../assets/logos";

const logos = [
  VisaLogo,
  MastercardLogo,
  ApplePayLogo,
  GooglePayLogo,
  PaypalLogo,
  AmexLogo,
  JcbLogo,
  UnionPayLogo,
  DinnerClubLogo,
  DiscoverLogo,
];

const LogoList = () => {
  return (
    <ul className={s.logos}>
      {logos.map((Logo, index) => (
        <li key={index}>
          <Logo width="100%" height="100%" />
        </li>
      ))}
    </ul>
  );
};

export default LogoList;
