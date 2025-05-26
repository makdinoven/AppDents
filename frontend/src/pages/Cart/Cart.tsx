import s from "./Cart.module.scss";
import { useLocation, useNavigate } from "react-router-dom";
import { Fragment, useEffect, useState } from "react";
import { Path } from "../../routes/routes.ts";
import { Trans } from "react-i18next";
import ModalCloseButton from "../../components/ui/ModalCloseButton/ModalCloseButton.tsx";
import CartItem from "./CartItem/CartItem.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";

const Cart = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(location.pathname === Path.cart);
  const [isClosing, setIsClosing] = useState(false);
  const isLogged = useSelector(
    (state: AppRootStateType) => state.user.isLogged,
  );
  const { items, quantity } = useSelector(
    (state: AppRootStateType) => state.cart,
  );
  const isCartEmpty = quantity === 0;
  const isPayDisabled = false;

  useEffect(() => {
    if (location.pathname === Path.cart) {
      setIsVisible(true);
    }
  }, [location.pathname]);

  const closeCart = () => {
    setIsClosing(true);
    setTimeout(() => {
      setIsClosing(false);
      setIsVisible(false);
      if (location.state?.backgroundLocation) {
        navigate(-1);
      } else {
        navigate(Path.main);
      }
    }, 300);
  };

  useEffect(() => {
    if (!isVisible) return;

    const handleEscape = (e: KeyboardEvent) =>
      e.key === "Escape" && closeCart();
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isVisible]);

  const cartFooterSections = [
    {
      label: <Trans i18nKey="cart.balance" />,
      value: 100,
      line: false,
      show: isLogged,
    },
    {
      label: <Trans i18nKey="cart.subtotal" />,
      value: 100,
      line: true,
      show: true,
    },
    {
      label: <Trans i18nKey="cart.discount" />,
      value: 100,
      line: true,
      show: true,
    },
    {
      label: <Trans i18nKey="cart.total" />,
      value: 100,
      line: false,
      valueClass: isPayDisabled ? s.red : s.blue,
      show: true,
    },
  ];

  const handlePay = () => {
    console.log("pay");
  };

  const handleDeleteCartItem = (id: number) => {
    console.log(id);
    // cartStorage.removeItem(id);
  };

  if (!isVisible) return null;

  return (
    <div
      className={`${s.cart_overlay} ${isClosing ? s.closing : s.open}`}
      onClick={closeCart}
    >
      <div
        className={`${s.cart} ${isCartEmpty ? s.empty : ""} ${isClosing ? s.closing : ""}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={s.cart_header}>
          <ModalCloseButton className={s.close_button} onClick={closeCart} />
          {!isCartEmpty && (
            <h2 className={s.cart_title}>
              <Trans i18nKey="cart.title" values={{ count: quantity }} />
            </h2>
          )}
        </div>

        {!isCartEmpty ? (
          <ul className={s.cart_items}>
            {items.map((item, i) => (
              <CartItem
                loading={false}
                key={i}
                item={item}
                type={"LANDING"}
                onDelete={handleDeleteCartItem}
              />
            ))}
          </ul>
        ) : (
          <>
            <div className={s.empty_container}>
              <h2>
                <Trans i18nKey={"cart.empty.title"} />
              </h2>
              <p>
                <Trans i18nKey={"cart.empty.haventAdded"} />
              </p>
            </div>
            <button className={`${s.btn} ${s.pay_btn}`} onClick={closeCart}>
              <Trans i18nKey={"cart.returnToShop"} />
            </button>
          </>
        )}
        {!isCartEmpty && (
          <div className={s.cart_footer}>
            <ul>
              {cartFooterSections.map((sec, i) => {
                if (!sec.show) return null;

                return (
                  <Fragment key={i}>
                    <li>
                      <span>{sec.label}</span>
                      <span
                        className={`${sec.valueClass ? sec.valueClass : ""}`}
                      >
                        ${sec.value}
                      </span>
                    </li>
                    {sec.line && (
                      <li>
                        <span className={s.line}></span>
                      </li>
                    )}
                  </Fragment>
                );
              })}
            </ul>
            <div className={s.cart_footer_btns}>
              <button
                disabled={isPayDisabled}
                onClick={handlePay}
                className={`${s.btn} ${s.pay_btn} ${isPayDisabled ? s.disabled : ""} `}
              >
                <Trans i18nKey={"pay"} />
              </button>
              {/*<button*/}
              {/*  onClick={handleReplenish}*/}
              {/*  className={`${s.btn} ${s.replenish_btn}`}*/}
              {/*>*/}
              {/*  <Trans i18nKey={"cart.replenish"} />*/}
              {/*</button>*/}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Cart;
