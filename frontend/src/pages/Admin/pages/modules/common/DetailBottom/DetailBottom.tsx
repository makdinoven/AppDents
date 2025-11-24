import s from "./DetailBottom.module.scss";
import PrettyButton from "../../../../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";

const DetailBottom = ({
  deleteLabel,
  handleDelete,
  handleSave,
}: {
  deleteLabel: string;
  handleSave: any;
  handleDelete: any;
}) => {
  return (
    <div className={s.detail_bottom}>
      <PrettyButton
        variant={"primary"}
        text={t("admin.save")}
        onClick={handleSave}
      />
      <PrettyButton
        variant={"danger"}
        text={t(deleteLabel)}
        onClick={handleDelete}
      />
    </div>
  );
};

export default DetailBottom;
