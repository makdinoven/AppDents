import s from "./SidebarShell.module.scss";
import { SidebarData } from "@/shared/common/types/commonTypes.ts";
import { NavLink } from "react-router-dom";
import { Chevron } from "@/shared/assets/icons";
import { t } from "i18next";

interface SidebarShellProps {
  data: SidebarData[];
}

export const SidebarShell = ({ data }: SidebarShellProps) => {
  return (
    <div className={s.sidebar_shell}>
      {data.length > 0 &&
        data.map((item: SidebarData) => (
          <NavLink
            to={item.path}
            key={item.path}
            className={({ isActive }) =>
              `${s.sidebar_item} ${isActive ? s.active : ""}`
            }
          >
            <div className={s.item_content}>
              <span className={s.icon}>{item.icon}</span>
              <span className={s.title}>{t(item.title)}</span>
            </div>
            <Chevron className={s.arrow} />
          </NavLink>
        ))}
    </div>
  );
};
