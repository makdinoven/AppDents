import { useNavigate, useParams } from "react-router-dom";
import Loader from "../../../../components/ui/Loader/Loader.tsx";
import s from "./DetailPage.module.scss";
import DetailHeader from "../modules/common/DetailHeader/DetailHeader.tsx";
import DetailBottom from "../modules/common/DetailBottom/DetailBottom.tsx";
import { useEffect, useState } from "react";
import { adminApi } from "../../../../api/adminApi/adminApi.ts";
import { Alert } from "../../../../components/ui/Alert/Alert.tsx";
import { CheckMark, ErrorIcon } from "../../../../assets/icons";
import { mainApi } from "../../../../api/mainApi/mainApi.ts";
import { t } from "i18next";
import AdminField from "../modules/common/AdminField/AdminField.tsx";
import MultiSelect from "../../../../components/CommonComponents/MultiSelect/MultiSelect.tsx";
import { LANGUAGES } from "../../../../common/helpers/commonConstants.ts";
import PhotoUploader from "../../../../components/CommonComponents/PhotoUploader/PhotoUploader.tsx";
import PdfUploader from "../modules/common/PdfUploader/PdfUploader.tsx";

const BookDetail = () => {
  const navigate = useNavigate();
  const { bookId } = useParams();
  const [loading, setLoading] = useState(true);
  const [book, setBook] = useState<any>(null);
  const [tags, setTags] = useState<any>([]);
  const [authors, setAuthors] = useState<any>([]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [bookRes, tagsRes, authorsRes] = await Promise.all([
        adminApi.getBookDetail(bookId),
        mainApi.getTags(),
        adminApi.getAuthorsList({ size: 100000 }),
      ]);
      setTags(tagsRes.data);
      setBook(bookRes.data);
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

  useEffect(() => {
    if (bookId) {
      fetchAllData();
    }
  }, [bookId]);

  const handleUploadPhoto = (url: string) => {
    setBook((prev: any) => {
      if (!prev) return prev;
      return { ...prev, cover_url: url };
    });
  };

  const handleChange = (e: any) => {
    const { name, value } = e;
    setBook((prev: any) => {
      if (!prev) return prev;
      return { ...prev, [name]: value };
    });
  };

  const handleSave = async () => {
    try {
      await adminApi.updateBook(bookId, book);
      navigate(-1);
    } catch (error) {
      Alert(`Error updating book: ${error}`, <ErrorIcon />);
    }
  };

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
          <div className={s.list}>
            <AdminField
              type="input"
              id="title"
              placeholder={t("admin.books.title.placeholder")}
              label={t("admin.books.title")}
              value={book.title}
              onChange={handleChange}
            />
            <AdminField
              type="textarea"
              id="description"
              placeholder={t("admin.books.description.placeholder")}
              label={t("admin.books.description")}
              value={book.description ? book.description : ""}
              onChange={handleChange}
            />

            <PdfUploader itemId={book.id} files={book.files} />

            <div className={s.two_items}>
              <AdminField
                type="input"
                id="publication_date"
                placeholder={t("admin.books.publicationDate.placeholder")}
                label={t("admin.books.publicationDate")}
                value={book.publication_date ? book.publication_date : ""}
                onChange={handleChange}
              />
              <MultiSelect
                isSearchable={false}
                id={"language"}
                options={LANGUAGES}
                placeholder={"Choose a language"}
                label={t("admin.landings.language")}
                selectedValue={book.language}
                isMultiple={false}
                onChange={handleChange}
                valueKey="value"
                labelKey="label"
              />
            </div>

            <div className={s.two_items}>
              {authors && (
                <MultiSelect
                  id={"author_ids"}
                  options={authors}
                  placeholder={"Choose an author"}
                  label={t("admin.landings.authors")}
                  selectedValue={book.author_ids}
                  isMultiple={true}
                  onChange={handleChange}
                  valueKey="id"
                  labelKey="name"
                />
              )}
              {tags && (
                <MultiSelect
                  id={"tag_ids"}
                  options={tags}
                  placeholder={"Choose a tag"}
                  label={t("admin.landings.tags")}
                  selectedValue={book.tag_ids}
                  isMultiple={true}
                  onChange={handleChange}
                  valueKey="id"
                  labelKey="name"
                />
              )}
            </div>

            <PhotoUploader
              onUpload={handleUploadPhoto}
              url={book.cover_url}
              type="book"
              dataId={book.id}
              id="cover_url"
              title={t("admin.landings.mainImage")}
              label={t("admin.landings.mainImage.choose")}
            />

            <DetailBottom
              deleteLabel={"admin.books.delete"}
              handleSave={handleSave}
              handleDelete={handleDeleteBook}
            />
          </div>
        )
      )}
    </div>
  );
};

export default BookDetail;
