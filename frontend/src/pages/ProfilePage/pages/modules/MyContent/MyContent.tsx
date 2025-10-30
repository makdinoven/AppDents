import s from "./MyContent.module.scss";
import { Trans } from "react-i18next";
import SectionHeader from "../../../../../components/ui/SectionHeader/SectionHeader.tsx";
import { Path } from "../../../../../routes/routes.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../../../../store/store.ts";
import CourseCardSkeletons from "../../../../../components/ui/Skeletons/CourseCardSkeletons/CourseCardSkeletons.tsx";
import ProfileEntityCard from "../ProfileEntityCard/ProfileEntityCard.tsx";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const MyContent = ({
  items,
  type = "course",
}: {
  items: any[];
  type?: "book" | "course";
}) => {
  const loading = useSelector((state: AppRootStateType) =>
    type === "course" ? state.user.loadingCourses : state.user.loadingBooks,
  );
  const navigate = useNavigate();

  useEffect(() => {}, [type]);
  return (
    <section className={s.content}>
      <SectionHeader
        name={type === "course" ? "profile.yourCourses" : "profile.yourBooks"}
      />
      {loading ? (
        <CourseCardSkeletons amount={6} columns={3} />
      ) : (
        <ul
          className={`${s.content_list} ${type === "book" ? s.book : ""} ${items.length <= 0 && s.no_items}`}
        >
          {items.length > 0 ? (
            items.map((item: any, index: number) => (
              <ProfileEntityCard
                index={index}
                isPartial={type === "course" && item.access_level === "partial"}
                isOffer={
                  type === "course" && item.access_level === "special_offer"
                }
                viewText={type === "course" ? "viewCourse" : "viewBook"}
                key={`${type}-${item.id}`}
                name={item.name || item.title}
                previewPhoto={item.preview || item.cover_url}
                link={`${type === "course" ? Path.myCourse : Path.myBook}/${item.id}`}
                expires_at={item.expires_at && item.expires_at}
                type={type}
              />
            ))
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
                      className={`${s.highlight}`}
                    />
                  ),
                }}
              />
            </p>
          )}
        </ul>
      )}
    </section>
  );
};

export default MyContent;
