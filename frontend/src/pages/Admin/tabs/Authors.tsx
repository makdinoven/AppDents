import { Path } from "../../../routes/routes.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import {
  createAuthor,
  getAuthors,
} from "../../../store/actions/adminActions.ts";
import { INITIAL_AUTHOR } from "../../../common/helpers/commonConstants.ts";

const Authors = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const authors = useSelector((state: AppRootStateType) => state.admin.authors);
  const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        items={authors}
        searchField="name"
        itemName="name"
        itemLink={(author) => `${Path.authorDetail}/${author.id}`}
        loading={loading}
        onFetch={() => dispatch(getAuthors())}
        onCreate={() => dispatch(createAuthor(INITIAL_AUTHOR))}
        searchPlaceholder="admin.authors.search"
        createButtonText="admin.authors.create"
        notFoundText="admin.authors.notFound"
      />
    </>
  );
};

export default Authors;
