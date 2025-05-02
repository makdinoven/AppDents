import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";
import {
  createLanding,
  getLandings,
  searchLandings,
} from "../../../store/actions/adminActions.ts";
import { INITIAL_LANDING } from "../../../common/helpers/commonConstants.ts";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import { ParamsType } from "../../../api/adminApi/types.ts";

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
        data={landings}
        itemName={"landing_name"}
        itemLink={(landing) => `${Path.landingDetail}/${landing.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => dispatch(getLandings(params))}
        onSearch={(params: ParamsType) => dispatch(searchLandings(params))}
        onCreate={() => dispatch(createLanding(INITIAL_LANDING))}
        showToggle={true}
        handleToggle={(id: number, isHidden: boolean) =>
          handleToggleLandingVisibility(id, isHidden)
        }
      />
    </>
  );
};

export default Landings;
