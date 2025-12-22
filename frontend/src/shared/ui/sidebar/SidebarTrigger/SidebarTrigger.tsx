import s from "./SidebarTrigger.module.scss";
import Button from "@/shared/components/ui/Button/Button";
import { ArrowX, BurgerMenuIcon } from "@/shared/assets/icons";

type Props = {
  isOpen: boolean;
  onClick?: () => void;
  text?: string;
  className?: string;
};

export const SidebarTrigger = ({
  isOpen,
  onClick,
  text = "profile.menu",
  className,
}: Props) => {
  return (
    <Button
      iconLeft={isOpen ? <ArrowX /> : <BurgerMenuIcon />}
      onClick={onClick}
      text={text}
      className={`${s.menu_button} ${className ? className : ""}`}
      type="button"
    />
  );
};
