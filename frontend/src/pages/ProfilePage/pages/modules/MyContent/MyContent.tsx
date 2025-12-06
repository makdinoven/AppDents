import s from "./MyContent.module.scss";
import { Trans } from "react-i18next";
import SectionHeader from "../../../../../shared/components/ui/SectionHeader/SectionHeader.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../shared/store/store.ts";
import CourseCardSkeletons from "../../../../../shared/components/ui/Skeletons/CourseCardSkeletons/CourseCardSkeletons.tsx";
import ProfileEntityCard from "../ProfileEntityCard/ProfileEntityCard.tsx";
import { useNavigate, useSearchParams } from "react-router-dom";
import Search from "../../../../../shared/components/ui/Search/Search.tsx";
import { PATHS } from "../../../../../app/routes/routes.ts";

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
  const [searchParams, setSearchParams] = useSearchParams();
  const searchValue = searchParams.get(searchKey);
  const filteredItems = items.filter((item) => {
    if (!searchValue) return true;
    const field = type === "book" ? item.title : item.name;
    return field?.toLowerCase().includes(searchValue);
  });

  const handleSearch = (val: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(searchKey, val);
    setSearchParams(newParams);
  };

  return (
    <section className={s.content}>
      <SectionHeader
        name={type === "course" ? "profile.yourCourses" : "profile.yourBooks"}
      />
      {showSearch && items.length > 0 && (
        <Search
          valueFromUrl={searchValue ?? ""}
          onChangeValue={handleSearch}
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
                link={
                  type === "course"
                    ? PATHS.PROFILE_MY_COURSE.build(item.id)
                    : PATHS.PROFILE_MY_BOOK.build(item.id)
                }
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
                    navigate(
                      type === "course"
                        ? PATHS.COURSES_LISTING
                        : PATHS.BOOKS_LISTING,
                    )
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
