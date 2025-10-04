import s from "./AdControlMain/AdControlMain.module.scss";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../../api/adminApi/adminApi.ts";
import Loader from "../../../../../components/ui/Loader/Loader.tsx";
import AdControlItem from "./AdControlItem/AdControlItem.tsx";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import LoaderOverlay from "../../../../../components/ui/LoaderOverlay/LoaderOverlay.tsx";

const AdControlAccounts = () => {
  const [accountsList, setAccountsList] = useState<
    { id: number; name: string }[] | null
  >(null);
  const [loading, setLoading] = useState(true);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getAdAccountsList();
      setAccountsList(res.data);
      setLoading(false);
    } catch (error) {
      console.error(error);
    }
  };

  const handleCreateItem = async () => {
    setLoading(true);
    try {
      await adminApi.createAdAccount("New ad account");
      fetchAccounts();
    } catch (error) {
      setLoading(false);
      console.error(error);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  return loading && !accountsList ? (
    <Loader />
  ) : (
    <div className={s.ad_control_list}>
      {loading && <LoaderOverlay />}
      <PrettyButton text={"create"} onClick={() => handleCreateItem()} />
      {accountsList &&
        accountsList.map((accounts) => (
          <AdControlItem
            key={accounts.id}
            updateApi={adminApi.updateAdAccount}
            deleteApi={adminApi.deleteAdAccount}
            fetchListData={fetchAccounts}
            type={"account"}
            data={accounts}
          />
        ))}
    </div>
  );
};

export default AdControlAccounts;
