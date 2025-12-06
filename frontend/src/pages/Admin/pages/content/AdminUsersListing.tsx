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
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { PATHS } from "../../../../app/routes/routes.ts";

const AdminUsersListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const users = useSelector((state: AppRootStateType) => state.admin.users);
  const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        transKey={"users"}
        data={users}
        itemName={"email"}
        itemLink={(user) => PATHS.ADMIN_USER_DETAIL.build(user.id)}
        loading={loading}
        onSearch={(params) => dispatch(searchUsers(params))}
        onLoad={(params) => dispatch(getUsers(params))}
        onCreate={() => dispatch(createUser(INITIAL_USER))}
      />
    </>
  );
};

export default AdminUsersListing;
