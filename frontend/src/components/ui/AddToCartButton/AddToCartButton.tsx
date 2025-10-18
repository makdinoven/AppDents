import s from "./AddToCartButton.module.scss";
import { CartIcon, CheckMarkIcon } from "../../../assets/icons";
import LoaderOverlay from "../LoaderOverlay/LoaderOverlay.tsx";
import { Trans } from "react-i18next";

const AddToCartButton = ({
  loading,
  isInCart,
  variant = "default",
  hasText,
  className,
  toggleCartItem,
}: {
  hasText?: boolean;
  className?: string;
  variant?: "default" | "primary";
  loading: boolean;
  isInCart: boolean;
  toggleCartItem: () => void;
}) => {
  return (
    <button
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleCartItem();
      }}
      className={`${className ? className : ""} ${s.btn} ${isInCart ? s.active : ""} ${s[variant]}`}
    >
      {loading && <LoaderOverlay inset={2} />}
      {!isInCart ? (
        <>
          {hasText && <Trans i18nKey="cart.addToCart" />}
          <CartIcon />
        </>
      ) : (
        <>
          <Trans i18nKey="cart.inCart" />
          <CheckMarkIcon />
        </>
      )}
    </button>
  );
};

export default AddToCartButton;
