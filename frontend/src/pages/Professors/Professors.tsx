import s from "./Professors.module.scss";
import { useState } from "react";
import { mainApi } from "../../shared/api/mainApi/mainApi.ts";
import ProfessorsList from "../../shared/components/ProfessorsList/ProfessorsList.tsx";
import ProductsSection from "../../shared/components/ProductsSection/ProductsSection.tsx";
import ListController from "../../shared/components/list/ListController/ListController.tsx";
import { ParamsType } from "../../shared/api/adminApi/types.ts";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../shared/store/store.ts";
import ProfessorCardSkeletons from "../../shared/components/ui/Skeletons/ProfessorCardSkeletons/ProfessorCardSkeletons.tsx";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";

const SIZE = 12;

const Professors = () => {
  const language = useSelector(
    (state: AppRootStateType) => state.user.language,
  );
  const [professors, setProfessors] = useState([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);

  const loadProfessors = async ({ page, language, q, size }: ParamsType) => {
    setLoading(true);
    try {
      let res;
      if (q) {
        const params = { language, page, size, q };
        res = await mainApi.searchProfessors(params);
      } else {
        const params = { language, page, size };
        res = await mainApi.getProfessors(params);
      }
      setProfessors(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
      setIsFirstLoad(false);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div lang={language.toLowerCase()} className={s.professors}>
      <DetailHeader title={"professor.professors.title"} />
      <ListController
        language={language}
        size={SIZE}
        type="professor"
        loadData={(params) => loadProfessors(params)}
        total={total}
        totalPages={totalPages}
        SkeletonComponent={ProfessorCardSkeletons}
        loading={loading}
      >
        <ProfessorsList professors={professors} loading={loading} />
      </ListController>
      {!isFirstLoad && (
        <ProductsSection
          productCardFlags={{ isOffer: true, isClient: true }}
          showSort={true}
          sectionTitle={"other.otherCourses"}
          pageSize={4}
        />
      )}
    </div>
  );
};

export default Professors;
