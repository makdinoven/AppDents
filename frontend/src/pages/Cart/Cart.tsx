import s from "./Cart.module.scss";
import { useNavigate } from "react-router-dom";

const Cart = () => {
  const navigate = useNavigate();

  const closeCart = () => {
    navigate(-1); // возвращает на предыдущую страницу
  };

  return (
    <div className={s.cart_overlay} onClick={closeCart}>
      <div className={s.cart} onClick={(e) => e.stopPropagation()}>
        <div className={s.cart_header}>
          <h2 className={s.cart_title}>Корзина</h2>
          <button className={s.close_button} onClick={closeCart}>
            &times;
          </button>
        </div>
        <div className={s.cart_items}>
          <div>Товар 1</div>
          <div>Товар 2</div>
        </div>
        <div className={s.cart_footer}>
          <button className={s.checkout_button}>Оформить заказ</button>
        </div>
      </div>
    </div>
  );
};

export default Cart;
