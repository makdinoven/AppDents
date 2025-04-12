import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";
import {
  createLanding,
  getLandings,
} from "../../../store/actions/adminActions.ts";
import { INITIAL_LANDING } from "../../../common/helpers/commonConstants.ts";
import { adminApi } from "../../../api/adminApi/adminApi.ts";

const Landings = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const landings = useSelector(
    (state: AppRootStateType) => state.admin.landings,
  );
  const dispatch = useDispatch<AppDispatchType>();

  const handleToggleLandingVisibility = (id: number, isHidden: boolean) => {
    try {
      adminApi.toggleLandingVisibility(id, isHidden);
    } catch (error) {
      console.log(error);
    }
  };

  return (
    <>
      <AdminList<any>
        items={landings}
        searchField="landing_name"
        itemName="landing_name"
        itemLink={(landing) => `${Path.landingDetail}/${landing.id}`}
        loading={loading}
        onFetch={() => dispatch(getLandings())}
        onCreate={() => dispatch(createLanding(INITIAL_LANDING))}
        searchPlaceholder="admin.landings.search"
        createButtonText="admin.landings.create"
        notFoundText="admin.landings.notFound"
        showToggle={true}
        handleToggle={(id: number, isHidden: boolean) =>
          handleToggleLandingVisibility(id, isHidden)
        }
      />
    </>
  );
};

export default Landings;
