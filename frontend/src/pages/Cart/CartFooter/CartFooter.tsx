import s from "./CartFooter.module.scss";
import CartProgressBar from "../CartProgressBar/CartProgressBar.tsx";
import { t } from "i18next";
import { Fragment } from "react";
import { Trans } from "react-i18next";
import { useForm } from "react-hook-form";
import { ChangePasswordType } from "../../../shared/api/userApi/types.ts";
import { joiResolver } from "@hookform/resolvers/joi";
import { emailSchema } from "../../../shared/common/schemas/emailSchema.ts";
import Form from "../../../shared/components/Modals/modules/Form/Form.tsx";
import { Percent } from "../../../shared/assets/icons/index.ts";
import LoaderOverlay from "../../../shared/components/ui/LoaderOverlay/LoaderOverlay.tsx";
import EmailInput from "../../../shared/components/ui/Inputs/EmailInput/EmailInput.tsx";
import UseBalanceOption from "../../../shared/components/ui/UseBalanceOption/UseBalanceOption.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../shared/store/store.ts";

type props = {
  paymentLoading?: boolean;
  balance: number;
  setIsBalanceUsed: (val: boolean) => void;
  isBalanceUsed: boolean;
  quantity: number;
  isLogged: boolean;
  handlePay: (form: any) => void;
};

const CartFooter = ({
  paymentLoading,
  balance,
  setIsBalanceUsed,
  isBalanceUsed,
  quantity,
  isLogged,
  handlePay,
}: props) => {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<ChangePasswordType>({
    resolver: isLogged ? undefined : joiResolver(emailSchema),
    mode: "onChange",
  });

  const {
    loading: previewLoading,
    current_discount,
    next_discount,
    total_amount,
    total_amount_with_balance_discount,
    total_new_amount,
    total_old_amount,
  } = useSelector((state: AppRootStateType) => state.cart);

  const email = watch("email");
  const isPayDisabled = !isLogged && (!email || !!errors.email);

  const handleCheckboxToggle = () => {
    if (balance! > 0) {
      setIsBalanceUsed(!isBalanceUsed);
    }
  };

  const cartFooterSections = [
    {
      label: (
        <span>
          <Trans
            i18nKey={"cart.priceWithoutDiscount"}
            values={{ count: quantity }}
          />
        </span>
      ),
      component: (
        <span>
          <span className="highlight">${total_new_amount}</span>{" "}
          <span className={`${s.old_price_total} crossed-15`}>
            ${total_old_amount}
          </span>
        </span>
      ),
      show: quantity > 1,
      line: true,
    },
    {
      label: (
        <>
          <Percent className={s.percent} />{" "}
          <Trans i18nKey="cart.balanceDiscount" />
        </>
      ),
      line: false,
      show: isLogged && isBalanceUsed,
      component: (
        <span className={s.blue}>
          - ${balance > total_amount ? total_amount : balance}
        </span>
      ),
    },
    {
      label: (
        <>
          <Percent className={s.percent} />{" "}
          <Trans i18nKey="cart.currentDiscount" />
        </>
      ),
      line: true,
      show: true,
      component: <span className={"highlight"}>- {current_discount}%</span>,
    },
    // {
    //   label: (
    //     <span className={s.balance}>
    //       <Trans i18nKey={"cart.useBalance"} />:{" "}
    //       <span className={s.blue}>${balance}</span>
    //     </span>
    //   ),
    //   show: isLogged,
    //   component: (
    //     <div className={s.balance_switch}>
    //       <ToggleCheckbox
    //         disabled={balance! === 0}
    //         variant={"small"}
    //         onChange={handleCheckboxToggle}
    //         isChecked={isBalanceUsed}
    //       />
    //     </div>
    //   ),
    //   line: true,
    // },
    {
      label: (
        <span>
          <Trans i18nKey="cart.total" />
          {isLogged && (
            <>
              :{" "}
              <span className={s.blue}>
                $
                {isBalanceUsed
                  ? total_amount_with_balance_discount
                  : total_amount}
              </span>
            </>
          )}
        </span>
      ),
      show: true,
      component: (
        <>
          {isLogged ? (
            <UseBalanceOption
              balance={balance}
              onToggle={handleCheckboxToggle}
              disabled={balance === 0}
              isChecked={isBalanceUsed}
            />
          ) : (
            <span className={s.blue}>
              $
              {isBalanceUsed
                ? total_amount_with_balance_discount
                : total_amount}
            </span>
          )}
        </>
      ),
    },
  ];

  return (
    <div className={s.cart_footer}>
      {previewLoading && <LoaderOverlay />}
      <CartProgressBar
        current_discount={current_discount}
        next_discount={next_discount}
        quantity={quantity}
      />
      <ul>
        {cartFooterSections.map((sec, i) => {
          if (!sec.show) return null;

          return (
            <Fragment key={i}>
              <li>
                <span className={s.label}>{sec.label}</span>
                <span className={s.values}>{sec.component}</span>
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

      <Form handleSubmit={handleSubmit(handlePay)}>
        {!isLogged && (
          <EmailInput
            isValidationUsed
            id="email"
            value={email}
            setValue={setValue}
            error={errors.email?.message}
            placeholder={t("email")}
            {...register("email")}
          />
        )}

        <button
          type="submit"
          disabled={isPayDisabled}
          className={`${s.btn} ${s.pay_btn} ${isPayDisabled ? s.disabled : ""} `}
        >
          {paymentLoading && <LoaderOverlay />}
          <Trans i18nKey={"pay"} />
        </button>

        {!isLogged && (
          <p className={s.warn_text}>
            <Trans i18nKey="paymentWarn" />
          </p>
        )}
      </Form>
    </div>
  );
};

export default CartFooter;
