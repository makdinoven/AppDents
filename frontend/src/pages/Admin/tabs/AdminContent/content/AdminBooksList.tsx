import { useDispatch, useSelector } from "react-redux";
import { createCourse } from "../../../../../store/actions/adminActions.ts";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../../store/store.ts";
import AdminList from "../../../modules/common/AdminList/AdminList.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { ParamsType } from "../../../../../api/adminApi/types.ts";

const AdminBooksList = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const books = useSelector((state: AppRootStateType) => state.admin.books);
  const dispatch = useDispatch<AppDispatchType>();

  const loadData = (params: ParamsType) => {
    if (params.q) {
      // dispatch(searchBooks(params));
    } else {
      // dispatch(getBooks(params));
    }
  };

  const INITIAL_BOOK = {};

  return (
    <>
      <AdminList<any>
        data={books}
        itemName={"name"}
        itemLink={(book) => `${Path.bookDetail}/${book.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createCourse(INITIAL_BOOK))}
      />
    </>
  );
};

export default AdminBooksList;
