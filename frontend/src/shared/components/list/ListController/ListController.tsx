import s from "./ListController.module.scss";
import { ReactNode } from "react";

type ListControllerProps = {
  size?: number;
  children: React.ReactNode;
  paginationSlot: ReactNode;
  filtersSlot: ReactNode;
};

const ListController = ({
  children,
  paginationSlot,
  filtersSlot,
}: ListControllerProps) => {
  return (
    <div className={s.list_controller_container}>
      {filtersSlot}

      {children}

      {paginationSlot && paginationSlot}
    </div>
  );
};

export default ListController;
