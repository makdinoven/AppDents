import s from "./CustomOrder.module.scss";
import { useForm } from "react-hook-form";
import { OrderDescriptionType } from "../../../api/userApi/types.ts";
import { Trans } from "react-i18next";
import Form from "../../Modals/modules/Form/Form.tsx";
import { t } from "i18next";
import Button from "../../ui/Button/Button.tsx";
import { useState } from "react";
import { SendIcon } from "../../../assets/icons";
import { ToothGreen } from "../../../assets";

const CustomOrder = () => {
  const handleOrderSubmit = () => {};
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<OrderDescriptionType>({ mode: "onSubmit" });
  const [loading, setLoading] = useState(false);

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
              <label htmlFor="description-input">
                <Trans i18nKey="describeProduct" />
              </label>
              <textarea
                id="description-input"
                name="description-input"
                placeholder={t("typeHere")}
                {...{ register: "description-input" }}
              />
              <ToothGreen />
            </div>
          </div>
          <Button
            type="submit"
            disabled={loading}
            loading={loading}
            icon={<SendIcon />}
            variant="filled_dark"
            className={s.request_btn}
          >
            <Trans i18nKey="request" />
          </Button>
        </Form>
      </div>
    </div>
  );
};
export default CustomOrder;
