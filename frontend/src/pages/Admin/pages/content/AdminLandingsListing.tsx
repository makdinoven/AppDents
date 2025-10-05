import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../../routes/routes.ts";
import {
  createLanding,
  getLandings,
  searchLandings,
} from "../../../../store/actions/adminActions.ts";
import { INITIAL_LANDING } from "../../../../common/helpers/commonConstants.ts";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { ParamsType } from "../../../../api/adminApi/types.ts";
import { toggleLandingVisibility } from "../../../../store/slices/adminSlice.ts";

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
        itemLink={(landing) => `${Path.landingDetail}/${landing.id}`}
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
