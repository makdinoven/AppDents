import ModalOverlay from "../../Modals/ModalOverlay/ModalOverlay.tsx";
import s from "./FiltersPanel.module.scss";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import { Filter } from "../types.ts";
import FilterItem from "./FilterItem.tsx";

type Props = {
  isFullScreen: boolean;
  setIsFullScreen: (fs: boolean) => void;
  filters: any;
  params: ListQueryParams;
  setParams: (next: Partial<ListQueryParams>) => void;
};

const FiltersPanelFullscreen = ({
  isFullScreen,
  setIsFullScreen,
  filters,
  params,
  setParams,
}: Props) => {
  const resetAll = () => {
    const cleared: Record<string, any> = {};

    // для всех текущих фильтров ставим undefined → useListQueryParams их удалит из URL
    Object.keys(params.filters).forEach((key) => {
      cleared[key] = undefined;
    });

    setParams({
      filters: cleared,
      page: 1,
    });
  };

  return (
    isFullScreen && (
      <ModalOverlay
        customHandleClose={() => setIsFullScreen(false)}
        isVisibleCondition={isFullScreen}
        modalPosition="right"
      >
        <div className={s.background}>
          <button className={s.reset_all_btn} onClick={resetAll}>
            Reset All
          </button>
          {Object.entries(filters).map(([key, filter]) => (
            <FilterItem
              key={key}
              filter={filter as Filter}
              params={params}
              setParams={setParams}
            />
          ))}
        </div>
      </ModalOverlay>
    )
  );
};

export default FiltersPanelFullscreen;
