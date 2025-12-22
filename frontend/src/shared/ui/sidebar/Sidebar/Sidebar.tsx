import s from "./Sidebar.module.scss";
import { RemoveScroll } from "react-remove-scroll";
import { ReactNode, useRef, useState } from "react";
import useOutsideClick from "@/shared/common/hooks/useOutsideClick.ts";
import { SidebarTrigger } from "@/shared/ui/sidebar/SidebarTrigger/SidebarTrigger";

interface SidebarProps<TItem> {
  menuButtonText?: string;
  menuButtonClassName?: string;
  sections: TItem[][];
  topSlot?: ReactNode;
  bottomSlot?: ReactNode;
  renderItem: (item: TItem, close: () => void) => ReactNode;
}

export const Sidebar = <TItem,>({
  menuButtonText,
  menuButtonClassName,
  sections,
  topSlot,
  bottomSlot,
  renderItem,
}: SidebarProps<TItem>) => {
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
    <>
      <SidebarTrigger
        isOpen={isOpen}
        text={menuButtonText}
        className={menuButtonClassName}
        onClick={toggleSidebar}
      />
      <RemoveScroll enabled={isOpen}>
        <div className={s.sidebar_wrapper} ref={sidebarRef}>
          <div className={s.sidebar_content}>
            <div className={`${s.sidebar} ${isOpen ? s.open : ""}`}>
              {topSlot && topSlot}
              {sections.length > 0 &&
                sections.map((section, i) => (
                  <div key={i} className={s.sidebar_section}>
                    {section.map((item) =>
                      renderItem(item, handleSidebarClose),
                    )}
                  </div>
                ))}
              {bottomSlot && bottomSlot}
            </div>
          </div>
        </div>
      </RemoveScroll>
    </>
  );
};
