import { Path } from "../../../routes/routes.ts";
import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import {
  createAuthor,
  getAuthors,
  searchAuthors,
} from "../../../store/actions/adminActions.ts";
import { INITIAL_AUTHOR } from "../../../common/helpers/commonConstants.ts";
import { ParamsType } from "../../../api/adminApi/types.ts";

const Authors = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const authors = useSelector((state: AppRootStateType) => state.admin.authors);
  const dispatch = useDispatch<AppDispatchType>();

  const loadData = (params: ParamsType) => {
    if (params.q) {
      dispatch(searchAuthors(params));
    } else {
      dispatch(getAuthors(params));
    }
  };

  return (
    <>
      <AdminList<any>
        data={authors}
        itemName={"name"}
        itemLink={(author) => `${Path.authorDetail}/${author.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createAuthor(INITIAL_AUTHOR))}
        showLanguageFilter={true}
      />
    </>
  );
};

export default Authors;
