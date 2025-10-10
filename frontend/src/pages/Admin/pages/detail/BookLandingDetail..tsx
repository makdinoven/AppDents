import { useNavigate, useParams } from "react-router-dom";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { Alert } from "../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../assets/icons";
import { useEffect, useState } from "react";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import s from "./DetailPage.module.scss";
import MultiSelect from "../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { LANGUAGES } from "../../../../common/helpers/commonConstants.ts";
import { t } from "i18next";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import AdminField from "../modules/common/AdminField/AdminField.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";

const BookLandingDetail = () => {
  const { bookId } = useParams();
  const [loading, setLoading] = useState(false);
  const [bookLanding, setBookLanding] = useState<any>(null);
  const [books, setBooks] = useState<any | null>(null);
  const [authors, setAuthors] = useState<any>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (bookId) {
      fetchAllData();
    }
  }, [bookId]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [landingRes, authorsRes, booksRes] = await Promise.all([
        adminApi.getBookLanding(bookId),
        adminApi.getAuthorsList({ size: 100000 }),
        adminApi.getBooksList({ size: 100000 }),
      ]);
      setBooks(booksRes.data.items);
      setBookLanding(landingRes.data);
      setAuthors(authorsRes.data.items);
    } catch (error: any) {
      Alert(
        `Error fetching landing data, error message: ${error.message}`,
        <ErrorIcon />,
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBookLanding = async () => {
    if (!confirm(`Are you sure you want to delete this book landing?`)) return;

    try {
      await adminApi.deleteBookLanding(bookId);
      Alert("Book landing deleted", <CheckMark />);
      navigate(-1);
    } catch (error) {
      Alert(`Error deleting book landing: ${error}`, <ErrorIcon />);
    }
  };

  const handleChange = (e: any) => {
    const { name, value } = e;
    setBookLanding((prev: any) => {
      if (!prev) return prev;
      return { ...prev, [name]: value };
    });
  };

  const handleSave = async () => {
    try {
      await adminApi.updateBookLanding(bookId, bookLanding);
      navigate(-1);
    } catch (error) {
      Alert(`Error updating book landing: ${error}`, <ErrorIcon />);
    }
  };

  return (
    <div className={s.detail_container}>
      <DetailHeader title={"admin.bookLandings.edit"} />

      {loading ? (
        <Loader />
      ) : (
        bookLanding && (
          <div className={s.list}>
            <AdminField
              type="input"
              id="landing_name"
              placeholder={t("admin.bookLandings.title.placeholder")}
              label={t("admin.bookLandings.title")}
              value={bookLanding.landing_name}
              onChange={handleChange}
            />

            <AdminField
              type="input"
              id="page_name"
              placeholder={t("admin.landings.pageName.placeholder")}
              label={t("admin.landings.pageName")}
              value={bookLanding.page_name}
              onChange={handleChange}
            />

            <div className={s.two_items}>
              <AdminField
                type="input"
                inputType="number"
                id="old_price"
                label={t("admin.landings.oldPrice")}
                placeholder="0"
                value={bookLanding.old_price ?? ""}
                onChange={handleChange}
              />
              <AdminField
                type="input"
                inputType="number"
                id="new_price"
                placeholder="0"
                label={t("admin.landings.price")}
                value={bookLanding.new_price ?? ""}
                onChange={handleChange}
              />
            </div>

            <div className={s.two_items}>
              {authors && (
                <MultiSelect
                  id={"authors"}
                  options={authors}
                  placeholder={"Choose an author"}
                  label={t("admin.landings.authors")}
                  selectedValue={bookLanding.authors}
                  isMultiple={true}
                  onChange={handleChange}
                  valueKey="id"
                  labelKey="name"
                />
              )}

              <MultiSelect
                isSearchable={false}
                id={"language"}
                options={LANGUAGES}
                placeholder={"Choose a language"}
                label={t("admin.landings.language")}
                selectedValue={bookLanding.language}
                isMultiple={false}
                onChange={handleChange}
                valueKey="value"
                labelKey="label"
              />
            </div>

            <div className={s.two_items}>
              <MultiSelect
                id={"book_ids"}
                options={books}
                placeholder={"Add book"}
                label={t("admin.books.books")}
                selectedValue={bookLanding.book_ids}
                isMultiple={true}
                onChange={handleChange}
                valueKey="id"
                labelKey="title"
              />
            </div>

            <DetailBottom
              deleteLabel={"admin.landings.delete"}
              handleSave={handleSave}
              handleDelete={handleDeleteBookLanding}
            />
          </div>
        )
      )}
    </div>
  );
};

export default BookLandingDetail;
