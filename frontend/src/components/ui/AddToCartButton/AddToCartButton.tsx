import s from "./AddToCartButton.module.scss";
import { CartIcon, CheckMarkIcon } from "../../../assets/logos/index";
import { useState } from "react";

const AddToCartButton = ({ handleClick }: { handleClick: () => void }) => {
  const [isActive, setIsActive] = useState<boolean>(false);

  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsActive(!isActive);
        handleClick();
      }}
      className={`${s.btn} ${isActive ? s.active : ""}`}
    >
      {!isActive ? <CartIcon /> : <CheckMarkIcon />}
    </button>
  );
};

export default AddToCartButton;
