import { useDispatch, useSelector } from "react-redux";
import {
  createBook,
  getBooks,
  searchBooks,
} from "../../../../store/actions/adminActions.ts";
import { AppDispatchType, AppRootStateType } from "../../../../store/store.ts";
import { Path } from "../../../../routes/routes.ts";
import { ParamsType } from "../../../../api/adminApi/types.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { generateId } from "../../../../common/helpers/helpers.ts";

const AdminBooksListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const books = useSelector((state: AppRootStateType) => state.admin.books);
  const dispatch = useDispatch<AppDispatchType>();

  const loadData = (params: ParamsType) => {
    if (params.q) {
      dispatch(searchBooks(params));
    } else {
      dispatch(getBooks(params));
    }
  };

  const INITIAL_BOOK = {
    title: `New Book-${generateId()}`,
    slug: "asdassda",
    cover_url: "",
    files: [],
  };

  return (
    <>
      <AdminList<any>
        data={books}
        transKey={"books"}
        itemName={"title"}
        itemLink={(book) => `${Path.bookDetail}/${book.id}`}
        loading={loading}
        onFetch={(params: ParamsType) => loadData(params)}
        onCreate={() => dispatch(createBook(INITIAL_BOOK))}
      />
    </>
  );
};

export default AdminBooksListing;
