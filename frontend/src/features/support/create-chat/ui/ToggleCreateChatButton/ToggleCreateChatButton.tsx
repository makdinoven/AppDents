import s from "./ToggleCreateChatButton.module.scss";
import Button from "@/shared/components/ui/Button/Button.tsx";
import { useLocation, useNavigate } from "react-router-dom";

type Props = {
  toCreate: string;
  toBack: string;
};

export const ToggleCreateChatButton = ({ toCreate, toBack }: Props) => {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isToBack = pathname.startsWith(toCreate);

  const handleClick = () => {
    if (isToBack) navigate(toBack);
    else navigate(toCreate);
  };

  return (
    <Button
      variant="primary"
      text={!isToBack ? "create question" : "cancel creation"}
      className={s.btn}
      onClick={handleClick}
    />
  );
};
