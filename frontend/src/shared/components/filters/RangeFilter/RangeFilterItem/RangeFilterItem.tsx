import s from "./RangeFilterItem.module.scss";
import { MinusIcon, PlusIcon } from "../../../../assets/icons";

const RangeFilterItem = ({
  min,
  max,
  id,
  actions,
  disabledMinus,
  disabledPlus,
  placeholder,
  value,
}: {
  min: string;
  max: string;
  id: string;
  value: string;
  placeholder: string;
  disabledMinus: boolean;
  disabledPlus: boolean;
  actions: {
    change: (v: string) => void;
    dec: () => void;
    inc: () => void;
  };
}) => {
  const { change, inc, dec } = actions;

  return (
    <div className={s.input_container}>
      <button
        disabled={disabledMinus}
        className={`${s.update_number_btn} ${disabledMinus ? s.inactive : ""}`}
        onClick={dec}
      >
        <MinusIcon />
      </button>

      <input
        type="number"
        id={id}
        min={min}
        max={max}
        placeholder={placeholder}
        value={value}
        onChange={(e) => change(e.target.value)}
      />
      <button
        disabled={disabledPlus}
        className={`${s.update_number_btn} ${disabledPlus ? s.inactive : ""}`}
        onClick={inc}
      >
        <PlusIcon />
      </button>
    </div>
  );
};

export default RangeFilterItem;
