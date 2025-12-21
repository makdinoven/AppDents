import s from "./Sidebar.module.scss";
import { RemoveScroll } from "react-remove-scroll";
import Button from "@/shared/components/ui/Button/Button.tsx";
import { ArrowX, BurgerMenuIcon } from "@/shared/assets/icons";
import { ReactNode, useRef, useState } from "react";
import useOutsideClick from "@/shared/common/hooks/useOutsideClick.ts";
import { SidebarShellData } from "@/shared/common/types/commonTypes.ts";
import { SidebarShell } from "@/shared/components/ui/sidebar/sidebar-shell/SidebarShell.tsx";

interface SidebarProps {
  menuButtonText?: string;
  menuButtonClassName?: string;
  sidebarShellsData: SidebarShellData[][];
  topSlot?: ReactNode;
  bottomSlot?: ReactNode;
}

export const Sidebar = ({
  menuButtonText,
  menuButtonClassName,
  sidebarShellsData,
  topSlot,
  bottomSlot,
}: SidebarProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const handleSidebarClose = () => {
    setIsOpen(false);
  };

  const toggleSidebar = () => {
    setIsOpen((prev) => !prev);
  };

  useOutsideClick(sidebarRef, () => {
    if (isOpen) handleSidebarClose();
  });

  return (
    <RemoveScroll enabled={isOpen}>
      <div className={s.sidebar_wrapper} ref={sidebarRef}>
        <Button
          iconLeft={isOpen ? <ArrowX /> : <BurgerMenuIcon />}
          onClick={toggleSidebar}
          text={menuButtonText}
          className={menuButtonClassName}
          type="button"
        />
        <div className={s.sidebar_content}>
          <div className={`${s.sidebar} ${isOpen ? s.open : ""}`}>
            {topSlot && topSlot}
            {sidebarShellsData.length > 0 &&
              sidebarShellsData.map((shell) => (
                <SidebarShell
                  data={[...shell]}
                  onItemClick={handleSidebarClose}
                />
              ))}
            {bottomSlot && bottomSlot}
          </div>
        </div>
      </div>
    </RemoveScroll>
  );
};
