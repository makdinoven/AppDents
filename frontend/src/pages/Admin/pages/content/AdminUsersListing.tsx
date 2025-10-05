<<<<<<<< HEAD:frontend/src/pages/Admin/tabs/AdminContent/content/AdminUsersList.tsx
import AdminList from "../../../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { INITIAL_USER } from "../../../../../common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../../store/store.ts";
========
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../../routes/routes.ts";
import { INITIAL_USER } from "../../../../common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../../store/store.ts";
>>>>>>>> main:frontend/src/pages/Admin/pages/content/AdminUsersListing.tsx
import {
  createUser,
  getUsers,
  searchUsers,
<<<<<<<< HEAD:frontend/src/pages/Admin/tabs/AdminContent/content/AdminUsersList.tsx
} from "../../../../../store/actions/adminActions.ts";
import { ParamsType } from "../../../../../api/adminApi/types.ts";

const AdminUsersList = () => {
========
} from "../../../../store/actions/adminActions.ts";
import { ParamsType } from "../../../../api/adminApi/types.ts";

const AdminUsersListing = () => {
>>>>>>>> main:frontend/src/pages/Admin/pages/content/AdminUsersListing.tsx
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
        itemLink={(user) => `${Path.userDetail}/${user.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createUser(INITIAL_USER))}
      />
    </>
  );
};

<<<<<<<< HEAD:frontend/src/pages/Admin/tabs/AdminContent/content/AdminUsersList.tsx
export default AdminUsersList;
========
export default AdminUsersListing;
>>>>>>>> main:frontend/src/pages/Admin/pages/content/AdminUsersListing.tsx
