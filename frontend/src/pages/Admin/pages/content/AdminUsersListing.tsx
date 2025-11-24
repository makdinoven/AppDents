import {
  createUser,
  getUsers,
  searchUsers,
} from "../../../../shared/store/actions/adminActions.ts";
import { INITIAL_USER } from "../../../../shared/common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../shared/store/store.ts";
import { ParamsType } from "../../../../shared/api/adminApi/types.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { PATHS } from "../../../../app/routes/routes.ts";

const AdminUsersListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const users = useSelector((state: AppRootStateType) => state.admin.users);
  const dispatch = useDispatch<AppDispatchType>();

  const loadData = (params: ParamsType) => {
    if (params.q) {
      dispatch(searchUsers(params));
    } else {
      dispatch(getUsers(params));
    }
  };

  return (
    <>
      <AdminList<any>
        transKey={"users"}
        data={users}
        itemName={"email"}
        itemLink={(user) => PATHS.ADMIN_USER_DETAIL.build(user.id)}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createUser(INITIAL_USER))}
      />
    </>
  );
};

export default AdminUsersListing;
