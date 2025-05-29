import s from "./AddToCartButton.module.scss";
import { CartIcon, CheckMarkIcon } from "../../../assets/logos/index";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";
import { Trans } from "react-i18next";

const AddToCartButton = ({
  handleClick,
  isActive,
  loading,
}: {
  handleClick: () => void;
  isActive: boolean;
  loading: boolean;
}) => {
  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        handleClick();
      }}
      className={`${s.btn} ${isActive ? s.active : ""}`}
    >
      {loading && <LoaderOverlay inset={2} />}
      {!isActive ? (
        <CartIcon />
      ) : (
        <>
          <Trans i18nKey={"cart.inCart"} />
          <CheckMarkIcon />
        </>
      )}
    </button>
  );
};

export default AddToCartButton;
