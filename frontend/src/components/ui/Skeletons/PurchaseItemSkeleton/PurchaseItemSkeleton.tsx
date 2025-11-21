import s from "./PurchaseItemSkeleton.module.scss";

const PurchaseItemSkeleton: React.FC = () => {
  return (
    <div className={s.purchase_item}>
      <h3 className={s.purchase_item_header}></h3>
      <div className={s.purchases_container}>
        {Array(3)
          .fill({ length: 3 })
          .map((_, index) => {
            return (
              <li key={index} className={s.purchase}>
                <div className={s.operation_icon}></div>
                <div className={s.purchase_content}>
                  <div className={s.purchase_info_container}>
                    <p className={s.purchase_type}></p>
                    <div className={s.purchase_info}></div>
                  </div>
                  <div className={s.purchase_details_container}>
                    <div className={s.purchase_sum}></div>
                    <div className={s.date}></div>
                  </div>
                </div>
              </li>
            );
          })}
      </div>
    </div>
  );
};

export default PurchaseItemSkeleton;
