import s from "./Professors.module.scss";
import Search from "../../components/ui/Search/Search.tsx";
import { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import ProfessorsList from "../../components/CommonComponents/ProfessorsList/ProfessorsList.tsx";
import { Trans } from "react-i18next";
import Pagination from "../../components/ui/Pagination/Pagination.tsx";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import { useSearchParams } from "react-router-dom";
import useDebounce from "../../common/hooks/useDebounce.ts";
import CoursesSection from "../../components/CommonComponents/CoursesSection/CoursesSection.tsx";

const Professors = () => {
  const [professors, setProfessors] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const [loading, setLoading] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const pageFromUrl = parseInt(searchParams.get("page") || "1");
  const prevLanguageRef = useRef(language);
  const [searchValue, setSearchValue] = useState("");
  const debouncedSearchValue = useDebounce(searchValue, 300);
  const isFirstRender = useRef(true);

  useEffect(() => {
    if (prevLanguageRef.current !== language) {
      setSearchParams({ page: "1" });
      prevLanguageRef.current = language;
    }
  }, [language]);

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    if (pageFromUrl !== 1) {
      setSearchParams({ page: "1" });
    } else {
      loadProfessors(debouncedSearchValue);
    }
  }, [debouncedSearchValue]);

  useEffect(() => {
    loadProfessors(debouncedSearchValue);
  }, [language, pageFromUrl]);

  const loadProfessors = async (search?: string) => {
    setLoading(true);
    try {
      let res;
      if (search) {
        const params = { language, page: pageFromUrl, size: 10, q: search };
        res = await mainApi.searchProfessors(params);
      } else {
        const params = { language, page: pageFromUrl, size: 10 };
        res = await mainApi.getProfessors(params);
      }
      setProfessors(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={s.professors}>
      <DetailHeader title={"professor.professors.title"} />
      <div className={s.search_container}>
        <Search
          placeholder={"professor.search"}
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
        />
        {!!total && (
          <p>
            <Trans
              i18nKey={"professor.professorsFound"}
              values={{ count: total }}
            />
          </p>
        )}
      </div>
      <ProfessorsList professors={professors} loading={loading} />
      <Pagination totalPages={totalPages} />
      <CoursesSection
        showSort={true}
        sectionTitle={"other.otherCourses"}
        pageSize={4}
      />
    </div>
  );
};

export default Professors;
