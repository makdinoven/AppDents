import s from "./UseBalanceOption.module.scss";
import Checkbox from "../Checkbox/Checkbox.tsx";
import { Trans } from "react-i18next";

const UseBalanceOption = ({
  onToggle,
  disabled,
  isChecked,
  balance,
}: {
  balance: number;
  onToggle: () => void;
  disabled: boolean;
  isChecked: boolean;
}) => {
  return (
    <div
      onClick={onToggle}
      className={`${s.balance_container} ${disabled ? s.disabled : ""}`}
    >
      <Checkbox disabled={disabled} onChange={onToggle} isChecked={isChecked} />
      <p>
        <Trans i18nKey="cart.useBalance" /> <span> ${balance}</span>
      </p>
      {/*<div className={`${s.tooltip} ${isChecked ? s.visible : ""}`}>*/}
      {/*  <QuestionMark />*/}
      {/*  <Trans*/}
      {/*    i18nKey="cart.balanceWillBeUsed"*/}
      {/*    values={{ value: valueFromBalance }}*/}
      {/*  />*/}
      {/*</div>*/}
    </div>
  );
};

export default UseBalanceOption;
