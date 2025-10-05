import s from "./AdControlItem.module.scss";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { useState } from "react";
import LoaderOverlay from "../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";
import AdminField from "../../modules/common/AdminField/AdminField.tsx";

const AdControlItem = ({
  type,
  data,
  updateApi,
  deleteApi,
  fetchListData,
}: {
  type: "account" | "staff";
  data: any;
  updateApi: any;
  deleteApi: any;
  fetchListData: any;
}) => {
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [updatedName, setUpdateName] = useState(data.name);

  const handleUpdate = async () => {
    setLoading(true);
    try {
      await updateApi({ id: data.id, name: updatedName });
      await fetchListData();
      setEditMode(false);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      setEditMode(false);
      console.error(error);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Are you sure you want to delete this ${type}?`)) return;
    setLoading(true);
    try {
      await deleteApi(data.id);
      await fetchListData();
      setEditMode(false);
      setLoading(false);
    } catch (error) {
      setLoading(false);
      setEditMode(false);
      console.error(error);
    }
  };

  return (
    <div className={s.item}>
      {loading && <LoaderOverlay />}
      <span className={s.type}>
        {type} {data.id}
      </span>
      <div className={s.item_body}>
        {!editMode ? (
          <span>{data.name}</span>
        ) : (
          <AdminField
            className={s.input}
            type={"input"}
            id={`${data.id}-${data.type}-name}`}
            value={updatedName}
            onChange={(e: any) => setUpdateName(e.value)}
          />
        )}

        <div className={s.buttons}>
          {!editMode && (
            <PrettyButton
              onClick={() => setEditMode(true)}
              text={"edit"}
              variant={"default"}
            />
          )}
          {editMode && (
            <PrettyButton
              onClick={handleUpdate}
              text={"save"}
              variant={"primary"}
            />
          )}
          <PrettyButton
            onClick={handleDelete}
            text={"delete"}
            variant={"danger"}
          />
        </div>
      </div>
    </div>
  );
};

export default AdControlItem;
