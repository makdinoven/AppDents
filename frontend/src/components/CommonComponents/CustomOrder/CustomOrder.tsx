import s from "./CustomOrder.module.scss";
import { useForm } from "react-hook-form";
import { OrderDescriptionType } from "../../../api/userApi/types.ts";
import { Trans } from "react-i18next";
import Form from "../../Modals/modules/Form/Form.tsx";

const CustomOrder = () => {
  const handleOrderSubmit = () => {};
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OrderDescriptionType>({ mode: "onSubmit" });
  return (
    <div className={s.custom_order_block}>
      <h2>
        <Trans
          i18nKey={"customOrder"}
          components={[<span className={s.highlight} />]}
        />
      </h2>
      <div className={s.form}>
        <Form handleSubmit={handleSubmit(handleOrderSubmit)}>
          <div className={s.content_block}>
            <h3>
              <Trans i18nKey={"customOrderText"} />
            </h3>
            <div className={s.description_block}>
              <label></label>
              <textarea></textarea>
            </div>
          </div>
        </Form>
      </div>
    </div>
  );
};
export default CustomOrder;
