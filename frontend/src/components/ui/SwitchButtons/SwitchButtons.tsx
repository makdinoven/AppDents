import s from "./SwitchButtons.module.scss";

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
          {mode}
        </button>
      ))}
    </div>
  );
};

export default SwitchButtons;
