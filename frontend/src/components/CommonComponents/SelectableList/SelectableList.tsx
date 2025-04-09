import s from "./SelectableList.module.scss";
import ToggleButton from "../../ui/ToggleButton/ToggleButton.tsx";

interface ItemType {
  name: string;
  value: string;
}

interface SelectableListProps {
  items: ItemType[];
  activeValue: string;
  onSelect: (val: string) => void;
}

const SelectableList = ({
  items,
  activeValue,
  onSelect,
}: SelectableListProps) => {
  return (
    <ul className={s.list}>
      {items.map((item, index: number) => (
        <li key={index}>
          <ToggleButton
            isActive={activeValue === item.value}
            onClick={() => onSelect(item.value)}
            text={item.name}
          />
        </li>
      ))}
    </ul>
  );
};

export default SelectableList;
