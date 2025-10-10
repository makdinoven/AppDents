import s from "./SwitchButtons.module.scss";
import { Trans } from "react-i18next";

type Props<T extends string> = {
  buttonsArr: readonly T[];
  activeValue: T;
  handleClick: (val: T) => void;
};

const SwitchButtons = <T extends string>({
  buttonsArr,
  activeValue,
  handleClick,
}: Props<T>) => {
  return (
    <div className={s.toggle_btns_container}>
      {buttonsArr.map((mode) => (
        <button
          key={mode}
          className={`${activeValue === mode ? s.active : ""}`}
          onClick={() => handleClick(mode)}
        >
          <Trans i18nKey={mode} />
        </button>
      ))}
    </div>
  );
};

export default SwitchButtons;
