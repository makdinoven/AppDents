import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import { useEffect, useState } from "react";
import AdControlItem from "./AdControlItem/AdControlItem.tsx";
import Loader from "../../../../shared/components/ui/Loader/Loader.tsx";
import s from "./AdControlListing/AdControlListing.module.scss";
import PrettyButton from "../../../../shared/components/ui/PrettyButton/PrettyButton.tsx";
import LoaderOverlay from "../../../../shared/components/ui/LoaderOverlay/LoaderOverlay.tsx";

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

  return (
    <>
      {loading && !staffList ? (
        <Loader />
      ) : (
        <div className={s.ad_control_list}>
          {loading && <LoaderOverlay />}

          <PrettyButton
            className={s.create_btn}
            variant={"primary"}
            text={"create"}
            onClick={() => handleCreateItem()}
          />

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
      )}
    </>
  );
};

export default AdControlStaff;
