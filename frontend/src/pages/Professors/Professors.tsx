import s from "./Professors.module.scss";
import Search from "../../components/ui/Search/Search.tsx";
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../store/store.ts";
import { mainApi } from "../../api/mainApi/mainApi.ts";
import ProfessorsList from "../../components/CommonComponents/ProfessorsList/ProfessorsList.tsx";
import { Trans } from "react-i18next";
import Pagination from "../../components/ui/Pagination/Pagination.tsx";
import DetailHeader from "../Admin/modules/common/DetailHeader/DetailHeader.tsx";
import { useSearchParams } from "react-router-dom";

const Professors = () => {
  const [professors, setProfessors] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const [searchParams, setSearchParams] = useSearchParams();
  console.log(searchParams.get("page"));
  const pageFromUrl = parseInt(searchParams.get("page") || "1");
  const [page, setPage] = useState(pageFromUrl);

  // useEffect(() => {
  //   setPage(1);
  // }, [language]);

  useEffect(() => {
    fetchProfessors();
  }, [language, page]);

  useEffect(() => {
    setSearchParams({ page: page.toString() });
  }, [page]);

  const fetchProfessors = async () => {
    const params = {
      language: language,
      page: page,
      size: 12,
    };
    try {
      const res = await mainApi.getProfessors(params);
      setProfessors(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (error) {
      console.log(error);
    }
  };

  return (
    <div className={s.professors}>
      <DetailHeader title={"professor.professors.title"} />
      <div className={s.search_container}>
        <Search
          placeholder={"professor.search"}
          value={""}
          onChange={() => console.log("search")}
        />
        <p>
          <Trans i18nKey={"professor.professorsFound"} /> : {total}
        </p>
      </div>

      <ProfessorsList professors={professors} />
      <div className={s.pagination}>
        <Pagination setPage={setPage} page={page} totalPages={totalPages} />
      </div>
    </div>
  );
};

export default Professors;
