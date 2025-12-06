import ModalOverlay from "../../Modals/ModalOverlay/ModalOverlay.tsx";
import FilterItem from "../FilterItem/FilterItem.tsx";
import { Filter, FilterActionsType } from "../model/types.ts";
import type { ListQueryParams } from "../../list/model/useListQueryParams.ts";
import s from "./FiltersPanelFullscreen.module.scss";
import { BackArrow } from "../../../assets/icons";
import { Trans } from "react-i18next";
import Button from "../../ui/Button/Button.tsx";
import ResetBtn from "../ResetBtn/ResetBtn.tsx";
import { t } from "i18next";
import { useRef } from "react";

type Props = {
  loading?: boolean;
  isOpen: boolean;
  onClose: () => void;
  totalItems: number;
  filters: Filter[];
  params: ListQueryParams;
  actions: FilterActionsType;
};

const FiltersPanelFullscreen = ({
  isOpen,
  loading,
  onClose,
  filters,
  totalItems,
  params,
  actions,
}: Props) => {
  const closeModalRef = useRef<() => void>(null);

  return (
    <ModalOverlay
      customHandleClose={onClose}
      isVisibleCondition={isOpen}
      modalPosition="right"
      onInitClose={(fn) => (closeModalRef.current = fn)}
    >
      <div className={s.background}>
        <div className={s.top}>
          <div className={s.buttons}>
            <button
              className={s.back_btn}
              onClick={() => closeModalRef?.current?.()}
            >
              <BackArrow />
              <Trans i18nKey="filters.filters" />
            </button>

            <ResetBtn text={"filters.resetAll"} onClick={actions.resetAll} />
          </div>
        </div>

        <div className={s.filters_container}>
          {filters.map((f) => (
            <FilterItem
              key={f.label}
              filter={f}
              params={params}
              actions={actions}
            />
          ))}
        </div>

        <div className={s.bottom}>
          <Button
            loading={loading}
            variant="primary"
            text={t("filters.showItems", { count: totalItems })}
            disabled={totalItems === 0}
            onClick={() => closeModalRef?.current?.()}
          />
        </div>
      </div>
    </ModalOverlay>
  );
};

export default FiltersPanelFullscreen;
