import { useDispatch, useSelector } from "react-redux";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../shared/store/store.ts";
import {
  createAuthor,
  getAuthors,
  searchAuthors,
} from "../../../../shared/store/actions/adminActions.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { INITIAL_AUTHOR } from "../../../../shared/common/helpers/commonConstants.ts";
import { PATHS } from "../../../../app/routes/routes.ts";

const AdminAuthorsListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const authors = useSelector((state: AppRootStateType) => state.admin.authors);
  const dispatch = useDispatch<AppDispatchType>();

  return (
    <>
      <AdminList<any>
        transKey={"authors"}
        data={authors}
        itemName={"name"}
        itemLink={(author) => PATHS.ADMIN_AUTHOR_DETAIL.build(author.id)}
        loading={loading}
        onSearch={(params) =>
          dispatch(searchAuthors({ ...params, sort: "id_desc" }))
        }
        onLoad={(params) =>
          dispatch(getAuthors({ ...params, sort: "id_desc" }))
        }
        onCreate={() => dispatch(createAuthor(INITIAL_AUTHOR))}
        showLanguageFilter={true}
      />
    </>
  );
};

export default AdminAuthorsListing;
