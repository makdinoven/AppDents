import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../routes/routes.ts";
import { INITIAL_USER } from "../../../common/helpers/commonConstants.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { createUser, getUsers } from "../../../store/actions/adminActions.ts";

const Users = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const users = useSelector((state: AppRootStateType) => state.admin.users);
  const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        items={users}
        searchField="email"
        itemName="email"
        itemLink={(user) => `${Path.userDetail}/${user.id}`}
        loading={loading}
        onFetch={() => dispatch(getUsers())}
        onCreate={() => dispatch(createUser(INITIAL_USER))}
        searchPlaceholder="admin.users.search"
        createButtonText="admin.users.create"
        notFoundText="admin.users.notFound"
      />
    </>
  );
};

export default Users;
