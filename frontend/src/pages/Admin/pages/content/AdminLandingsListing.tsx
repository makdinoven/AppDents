import { useDispatch, useSelector } from "react-redux";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../shared/store/store.ts";
import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import { toggleLandingVisibility } from "../../../../shared/store/slices/adminSlice.ts";
import { ParamsType } from "../../../../shared/api/adminApi/types.ts";
import {
  createLanding,
  getLandings,
  searchLandings,
} from "../../../../shared/store/actions/adminActions.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { INITIAL_LANDING } from "../../../../shared/common/helpers/commonConstants.ts";
import { PATHS } from "../../../../app/routes/routes.ts";

const AdminLandingsListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const landings = useSelector(
    (state: AppRootStateType) => state.admin.landings,
  );
  const dispatch = useDispatch<AppDispatchType>();

  const handleToggleLandingVisibility = (id: number, isHidden: boolean) => {
    try {
      adminApi.toggleLandingVisibility(id, isHidden);
      dispatch(toggleLandingVisibility({ id, isHidden }));
    } catch (error) {
      dispatch(toggleLandingVisibility({ id, isHidden: !isHidden }));
      console.log(error);
    }
  };

  const loadData = (params: ParamsType) => {
    if (params.q) {
      dispatch(searchLandings(params));
    } else {
      dispatch(getLandings(params));
    }
  };

  return (
    <>
      <AdminList<any>
        transKey={"landings"}
        data={landings}
        itemName={"landing_name"}
        itemLink={(landing) => PATHS.ADMIN_LANDING_DETAIL.build(landing.id)}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createLanding(INITIAL_LANDING))}
        showToggle={true}
        showLanguageFilter={true}
        handleToggle={(id: number, isHidden: boolean) =>
          handleToggleLandingVisibility(id, isHidden)
        }
      />
    </>
  );
};

export default AdminLandingsListing;
