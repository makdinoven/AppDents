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
import ModalWrapper from "../../../../components/Modals/ModalWrapper/ModalWrapper.tsx";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton.tsx";

type CoverCandidate = {
  id: number;
  blob: Blob;
  url: string;
  formData: FormData;
};

const BookDetail = () => {
  const navigate = useNavigate();
  const { bookId } = useParams();
  const [loading, setLoading] = useState(true);
  const [book, setBook] = useState<any>(null);
  const [tags, setTags] = useState<any>([]);
  const [authors, setAuthors] = useState<any>([]);
  const [coverCandidates, setCoverCandidates] = useState<CoverCandidate[]>([]);
  const [selectedBookCover, setSelectedBookCover] =
    useState<CoverCandidate | null>(null);

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

  const handleGetBookCoverCandidates = async () => {
    try {
      const fetchWithRetry = async (
        bookId: string,
        index: number,
        retries = 5,
      ): Promise<Blob> => {
        for (let attempt = 1; attempt <= retries; attempt++) {
          try {
            const res = await adminApi.getBookCoverCandidate(bookId, index);
            return res.data;
          } catch (err: any) {
            if (err?.response?.status === 404 && attempt < retries) {
              console.warn(
                `Attempt ${attempt} for candidate ${index} failed with 404, retrying...`,
              );
              await new Promise((r) => setTimeout(r, 500));
              continue;
            }
            throw err;
          }
        }
        throw new Error(
          `Failed to fetch candidate ${index} after ${retries} retries`,
        );
      };

      const requests = [1, 2, 3].map((i) => fetchWithRetry(bookId!, i));
      const blobs = await Promise.all(requests);

      const candidates = blobs.map((blob, i) => {
        const formData = new FormData();
        formData.append("file", blob);
        formData.append("entity_type", "book_cover");
        formData.append("entity_id", String(bookId));

        return {
          id: i,
          blob,
          url: URL.createObjectURL(blob),
          formData,
        };
      });

      setCoverCandidates(candidates);
    } catch (error) {
      Alert(`Error getting candidates after retries: ${error}`, <ErrorIcon />);
    }
  };

  const handleSelectBookCover = async (data: CoverCandidate) => {
    setSelectedBookCover(data);
  };

  const handleSetCover = async () => {
    if (!selectedBookCover) {
      Alert(`Please, select book cover`, <ErrorIcon />);
      return;
    }
    try {
      const res = await adminApi.uploadImageNew(selectedBookCover.formData);
      Alert(`Book cover changed`, <CheckMark />);
      setBook({ ...book, cover_url: res.data.url });
      setCoverCandidates([]);
    } catch (e) {
      Alert(`Error loading book cover image: ${e}`, <ErrorIcon />);
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

            <PdfUploader
              itemId={book.id}
              files={book.files}
              getCovers={handleGetBookCoverCandidates}
            />
            {coverCandidates.length > 0 && (
              <ModalWrapper
                title={"Select book cover"}
                cutoutPosition={"none"}
                isOpen={coverCandidates.length > 0}
                onClose={() => setCoverCandidates([])}
              >
                <div className={s.candidates_modal}>
                  <div className={s.images}>
                    {coverCandidates.map((c, i: number) => (
                      <img
                        className={`${c.id === selectedBookCover?.id ? s.active : ""}`}
                        onClick={() => handleSelectBookCover(c)}
                        key={i}
                        src={c.url}
                        alt=""
                      />
                    ))}
                  </div>

                  <PrettyButton
                    text={"Set cover img"}
                    onClick={handleSetCover}
                  />
                </div>
              </ModalWrapper>
            )}

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
