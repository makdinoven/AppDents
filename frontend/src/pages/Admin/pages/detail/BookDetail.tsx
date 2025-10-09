import { useNavigate, useParams } from "react-router-dom";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import s from "./DetailPage.module.scss";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { Alert } from "../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../assets/icons";

const BookDetail = () => {
  const navigate = useNavigate();
  const { bookId } = useParams();
  const [loading, setLoading] = useState(true);
  const [book, setBook] = useState<any>(null);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [bookRes] = await Promise.all([
        adminApi.getBook(bookId),
        // mainApi.getTags(),
        // adminApi.getAuthorsList({ size: 100000 }),
      ]);
      // setTags(tagsRes);
      setBook(bookRes.data);
      // setAuthors(authorsRes.data.items);
    } catch (error: any) {
      Alert(
        `Error fetching landing data, error message: ${error.message}`,
        <ErrorIcon />,
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (bookId) {
      fetchAllData();
    }
  }, [bookId]);

  const handleSave = async () => {};

  const handleDeleteBook = async () => {
    if (!confirm(`Are you sure you want to delete this book?`)) return;

    try {
      await adminApi.deleteBook(bookId);
      Alert("Book deleted", <CheckMark />);
      navigate(-1);
    } catch (error) {
      Alert(`Error deleting book: ${error}`, <ErrorIcon />);
    }
  };

  return (
    <div className={s.detail_container}>
      <DetailHeader title={"admin.books.edit"} />
      {loading ? (
        <Loader />
      ) : (
        book && (
          <>
            {" "}
            {/*<AdminField*/}
            {/*    type="input"*/}
            {/*    id="landing_name"*/}
            {/*    placeholder={t("admin.bookLandings.title.placeholder")}*/}
            {/*    label={t("admin.bookLandings.title")}*/}
            {/*    value={bookLanding.landing_name}*/}
            {/*    onChange={handleChange}*/}
            {/*/>*/}
            {/*<AdminField*/}
            {/*    type="input"*/}
            {/*    id="page_name"*/}
            {/*    placeholder={t("admin.landings.pageName.placeholder")}*/}
            {/*    label={t("admin.landings.pageName")}*/}
            {/*    value={bookLanding.page_name}*/}
            {/*    onChange={handleChange}*/}
            {/*/>*/}
            {/*<MultiSelect*/}
            {/*    isSearchable={false}*/}
            {/*    id={"language"}*/}
            {/*    options={LANGUAGES}*/}
            {/*    placeholder={"Choose a language"}*/}
            {/*    label={t("admin.landings.language")}*/}
            {/*    selectedValue={bookLanding.language}*/}
            {/*    isMultiple={false}*/}
            {/*    onChange={handleChange}*/}
            {/*    valueKey="value"*/}
            {/*    labelKey="label"*/}
            {/*/>*/}
            {/*{authors && (*/}
            {/*    <MultiSelect*/}
            {/*        id={"author_ids"}*/}
            {/*        options={authors}*/}
            {/*        placeholder={"Choose an author"}*/}
            {/*        label={t("admin.landings.authors")}*/}
            {/*        selectedValue={bookLanding.authors}*/}
            {/*        isMultiple={true}*/}
            {/*        onChange={handleChange}*/}
            {/*        valueKey="id"*/}
            {/*        labelKey="name"*/}
            {/*    />*/}
            {/*)}*/}
            {/*<MultiSelect*/}
            {/*  id={"tag_ids"}*/}
            {/*  options={tags}*/}
            {/*  placeholder={"Choose a tag"}*/}
            {/*  label={t("admin.landings.tags")}*/}
            {/*  selectedValue={bookLanding.tag_ids}*/}
            {/*  isMultiple={true}*/}
            {/*  onChange={handleChange}*/}
            {/*  valueKey="id"*/}
            {/*  labelKey="name"*/}
            {/*/>*/}
          </>
        )
      )}

      <DetailBottom
        deleteLabel={"admin.books.delete"}
        handleSave={handleSave}
        handleDelete={handleDeleteBook}
      />
    </div>
  );
};

export default BookDetail;
