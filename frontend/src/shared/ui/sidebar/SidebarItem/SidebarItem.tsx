import s from "./SidebarItem.module.scss";
import { NavLink } from "react-router-dom";
import { t } from "i18next";
import { Chevron } from "@/shared/assets/icons";
import { ReactNode } from "react";

type SidebarShellData = {
  path: string;
  title: string;
  icon?: ReactNode;
};

export const SidebarItem = ({
  item,
  onClick,
}: {
  item: SidebarShellData;
  onClick: () => void;
}) => {
  return (
    <NavLink
      to={item.path}
      key={item.path}
      className={({ isActive }) =>
        `${s.sidebar_item} ${isActive ? s.active : ""}`
      }
      onClick={onClick}
    >
      <div className={s.item_content}>
        {item.icon && <span className={s.icon}>{item.icon}</span>}
        <span className={s.title}>{t(item.title)}</span>
      </div>
      <Chevron className={s.arrow} />
    </NavLink>
  );
};
