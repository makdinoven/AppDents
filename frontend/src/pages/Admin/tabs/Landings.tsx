import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";
import {
  createLanding,
  getLandings,
} from "../../../store/actions/adminActions.ts";

const initialLanding = {
  landing_name: "New landing",
  tag_id: 1,
  old_price: 0,
  new_price: 0,
  sales_count: 0,
};

const Landings = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const landings = useSelector(
    (state: AppRootStateType) => state.admin.landings,
  );
  const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        items={landings}
        searchField="name"
        itemName="landing_name"
        itemLink={(landing) => `${Path.landingDetail}/${landing.id}`}
        loading={loading}
        onFetch={() => dispatch(getLandings())}
        onCreate={() => dispatch(createLanding(initialLanding))}
        searchPlaceholder="admin.landings.search"
        createButtonText="admin.landings.create"
        notFoundText="admin.landings.notFound"
      />
    </>
  );
};

export default Landings;
