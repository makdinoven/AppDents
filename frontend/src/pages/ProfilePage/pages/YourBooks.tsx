import { useDispatch, useSelector } from "react-redux";
import { AppDispatchType, AppRootStateType } from "../../../store/store.ts";
import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { getBooks } from "../../../store/actions/userActions.ts";
import MyContent from "./modules/MyContent/MyContent.tsx";

const YourBooks = () => {
  const dispatch = useDispatch<AppDispatchType>();
  const books = useSelector((state: AppRootStateType) => state.user.books);
  const location = useLocation();
  const childKey = location.pathname.slice(1);

  useEffect(() => {
    if (!books.length) dispatch(getBooks());
  }, []);

  return <MyContent key={childKey} items={books} type="book" />;
};

export default YourBooks;
