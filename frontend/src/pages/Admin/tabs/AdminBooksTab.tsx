import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import { adminApi } from "../../../api/adminApi/adminApi.ts";
import { toggleBookVisibility } from "../../../store/slices/adminSlice.ts";
import { ParamsType } from "../../../api/adminApi/types.ts";
import {
  createBook,
  getBooks,
  searchBooks,
} from "../../../store/actions/adminActions.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { INITIAL_BOOK } from "../../../common/helpers/commonConstants.ts";
import { Path } from "../../../routes/routes.ts";

const AdminBooksTab = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const books = useSelector((state: AppRootStateType) => state.admin.books);
  const dispatch = useDispatch<AppDispatchType>();

  const handleToggleBookVisibility = (id: number, isHidden: boolean) => {
    try {
      adminApi.toggleBookVisibility(id, isHidden);
      dispatch(toggleBookVisibility({ id, isHidden }));
    } catch (error) {
      dispatch(toggleBookVisibility({ id, isHidden: !isHidden }));
      console.log(error);
    }
  };

  const loadData = (params: ParamsType) => {
    if (params.q) {
      dispatch(searchBooks(params));
    } else {
      dispatch(getBooks(params));
    }
  };

  return (
    <>
      <AdminList<any>
        data={books}
        itemName={"landing_name"}
        itemLink={(book) => `${Path.bookDetail}/${book.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createBook(INITIAL_BOOK))}
        showToggle={true}
        showLanguageFilter={true}
        handleToggle={(id: number, isHidden: boolean) =>
          handleToggleBookVisibility(id, isHidden)
        }
      />
    </>
  );
};

export default AdminBooksTab;
