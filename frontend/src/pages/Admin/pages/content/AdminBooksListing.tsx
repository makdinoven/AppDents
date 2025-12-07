import { useDispatch, useSelector } from "react-redux";
import {
  createBook,
  getBooks,
  searchBooks,
} from "../../../../shared/store/actions/adminActions.ts";
import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../shared/store/store.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { generateId } from "../../../../shared/common/helpers/helpers.ts";
import { PATHS } from "../../../../app/routes/routes.ts";

const AdminBooksListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const books = useSelector((state: AppRootStateType) => state.admin.books);
  const dispatch = useDispatch<AppDispatchType>();

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
        itemLink={(book) => PATHS.ADMIN_BOOK_DETAIL.build(book.id)}
        loading={loading}
        onSearch={(params) => dispatch(searchBooks(params))}
        onLoad={(params) => dispatch(getBooks(params))}
        onCreate={() => dispatch(createBook(INITIAL_BOOK))}
      />
    </>
  );
};

export default AdminBooksListing;
