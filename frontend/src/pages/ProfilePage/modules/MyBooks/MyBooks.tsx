import s from "./MyBooks.module.scss";
import SectionHeader from "../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../store/store.ts";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import { Trans } from "react-i18next";

const MyBooks = ({ books }: { books: any }) => {
  const loading = useSelector(
    (state: AppRootStateType) => state.user.loadingCourses,
  );

  console.log(books);

  return (
    <section className={s.books}>
      <SectionHeader name={"profile.yourBooks"} />
      {loading ? (
        <Loader />
      ) : (
        <ul className={s.courses_list}>
          {books.length > 0 ? (
            books.map((book: any, index: number) => (
              <li key={index}>{book.name}</li>
            ))
          ) : (
            <p className={s.no_courses}>
              <Trans i18nKey="profile.noBooks" />
            </p>
          )}
        </ul>
      )}
    </section>
  );
};

export default MyBooks;
