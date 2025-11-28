import ModalOverlay from "../../Modals/ModalOverlay/ModalOverlay";
import FilterItem from "./FilterItem";
import { Filter } from "../types";
import type { ListQueryParams } from "../../list/model/useListQueryParams";
import s from "./FiltersPanel.module.scss";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  filters: Filter[];
  params: ListQueryParams;
  actions: {
    set: (next: Partial<ListQueryParams>) => void;
    reset: (key: string) => void;
    resetAll: () => void;
  };
};

const FiltersPanelFullscreen = ({
  isOpen,
  onClose,
  filters,
  params,
  actions,
}: Props) => {
  if (!isOpen) return null;

  return (
    <ModalOverlay
      customHandleClose={onClose}
      isVisibleCondition={isOpen}
      modalPosition="right"
    >
      <div className={s.background}>
        <button className={s.reset_all_btn} onClick={actions.resetAll}>
          Reset All
        </button>

        {filters.map((f) => (
          <FilterItem
            key={f.label}
            filter={f}
            params={params}
            actions={actions}
          />
        ))}
      </div>
    </ModalOverlay>
  );
};

export default FiltersPanelFullscreen;
