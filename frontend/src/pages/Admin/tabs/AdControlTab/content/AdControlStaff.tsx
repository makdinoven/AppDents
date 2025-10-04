import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import AdControlItem from "./AdControlItem/AdControlItem.tsx";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import s from "./AdControlMain/AdControlMain.module.scss";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import LoaderOverlay from "../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";

const AdControlStaff = () => {
  const [staffList, setStaffList] = useState<
    { id: number; name: string }[] | null
  >(null);
  const [loading, setLoading] = useState(true);

  const fetchStaff = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getAdStaffList();
      setStaffList(res.data);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const handleCreateItem = async () => {
    try {
      setLoading(true);
      await adminApi.createAdStaff("New staff");
      fetchStaff();
    } catch (error) {
      setLoading(false);
      console.error(error);
    }
  };

  useEffect(() => {
    fetchStaff();
  }, []);

  return loading && !staffList ? (
    <Loader />
  ) : (
    <div className={s.ad_control_list}>
      {loading && <LoaderOverlay />}
      <PrettyButton text={"create"} onClick={() => handleCreateItem()} />
      {staffList &&
        staffList.map((staff) => (
          <AdControlItem
            key={staff.id}
            updateApi={adminApi.updateAdStaff}
            deleteApi={adminApi.deleteAdStaff}
            fetchListData={fetchStaff}
            type={"staff"}
            data={staff}
          />
        ))}
    </div>
  );
};

export default AdControlStaff;
