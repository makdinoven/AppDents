import s from "./MyContent.module.scss";
import { Trans } from "react-i18next";
import SectionHeader from "../../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../store/store.ts";
import CourseCardSkeletons from "../../../../../components/ui/Skeletons/CourseCardSkeletons/CourseCardSkeletons.tsx";
import ProfileEntityCard from "../ProfileEntityCard/ProfileEntityCard.tsx";
import { useNavigate, useSearchParams } from "react-router-dom";
import Search from "../../../../../components/ui/Search/Search.tsx";

const MyContent = ({
  items,
  type = "course",
  showSearch = false,
}: {
  items: any[];
  showSearch?: boolean;
  type?: "book" | "course";
}) => {
  const searchKey = `${type}-search`;
  const loading = useSelector((state: AppRootStateType) =>
    type === "course" ? state.user.loadingCourses : state.user.loadingBooks,
  );
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const searchValue = searchParams.get(searchKey);
  const filteredItems = items.filter((item) => {
    if (!searchValue) return true;
    const field = type === "book" ? item.title : item.name;
    return field?.toLowerCase().includes(searchValue);
  });

  return (
    <section className={s.content}>
      <SectionHeader
        name={type === "course" ? "profile.yourCourses" : "profile.yourBooks"}
      />
      {showSearch && (
        <Search
          id={searchKey}
          placeholder={type === "course" ? "courses.search" : "books.search"}
        />
      )}

      {loading ? (
        <CourseCardSkeletons amount={6} columns={3} />
      ) : items.length > 0 ? (
        filteredItems.length > 0 ? (
          <ul className={`${s.content_list} ${type === "book" ? s.book : ""}`}>
            {filteredItems.map((item: any, index: number) => (
              <ProfileEntityCard
                key={`${type}-${item.id}`}
                index={index}
                isPartial={type === "course" && item.access_level === "partial"}
                isOffer={
                  type === "course" && item.access_level === "special_offer"
                }
                viewText={type === "course" ? "viewCourse" : "viewBook"}
                name={item.name || item.title}
                previewPhoto={item.preview || item.cover_url}
                link={`${type === "course" ? Path.myCourse : Path.myBook}/${item.id}`}
                expires_at={item.expires_at && item.expires_at}
                type={type}
              />
            ))}
          </ul>
        ) : (
          <p className={s.no_items_container}>
            <Trans i18nKey={`main.noItems.${type}`} />
          </p>
        )
      ) : (
        <p className={s.no_content}>
          <Trans
            i18nKey={
              type === "course" ? "profile.noCourses" : "profile.noBooks"
            }
            components={{
              1: (
                <span
                  onClick={() =>
                    navigate(type === "course" ? Path.courses : Path.books)
                  }
                  className={s.highlight}
                />
              ),
            }}
          />
        </p>
      )}
    </section>
  );
};

export default MyContent;
