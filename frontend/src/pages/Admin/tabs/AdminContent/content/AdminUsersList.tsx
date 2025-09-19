import AdminList from "../../../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { INITIAL_USER } from "../../../../../common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../../store/store.ts";
import {
  createUser,
  getUsers,
  searchUsers,
} from "../../../../../store/actions/adminActions.ts";
import { ParamsType } from "../../../../../api/adminApi/types.ts";

const AdminUsersList = () => {
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
        data={users}
        itemName={"email"}
        itemLink={(user) => `${Path.userDetail}/${user.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createUser(INITIAL_USER))}
      />
    </>
  );
};

export default AdminUsersList;
