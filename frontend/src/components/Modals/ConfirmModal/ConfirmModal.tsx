import s from "./ConfirmModal.module.scss";

const ConfirmModal = () => {
  return (
    <div className={s.overlay}>
      <div className={s.modal}>confirm</div>
    </div>
  );
};

export default ConfirmModal;
