import s from "./Professors.module.scss";
import { useEffect, useState } from "react";
import { mainApi } from "../../shared/api/mainApi/mainApi.ts";
import ProfessorsList from "../../shared/components/ProfessorsList/ProfessorsList.tsx";
import ProductsSection from "../../shared/components/ProductsSection/ProductsSection.tsx";
import ListController from "../../shared/components/list/ListController/ListController.tsx";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../shared/store/store.ts";
import ProfessorCardSkeletons from "../../shared/components/ui/Skeletons/ProfessorCardSkeletons/ProfessorCardSkeletons.tsx";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import FiltersPanel from "../../shared/components/filters/FiltersPanel/FiltersPanel.tsx";
import Pagination, {
  PaginationType,
} from "../../shared/components/list/Pagination/Pagination.tsx";
import {
  FiltersDataUI,
  SelectedUI,
} from "../../shared/components/filters/model/types.ts";
import { useListQueryParams } from "../../shared/components/list/model/useListQueryParams.ts";
import {
  mapBackendFilters,
  mapBackendSelected,
} from "../../shared/components/filters/model/mapBackendFilters.ts";

const Professors = () => {
  const { language } = useSelector((state: AppRootStateType) => state.user);
  const [professors, setProfessors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [filters, setFilters] = useState<FiltersDataUI | null>(null);
  const [selectedFilters, setSelectedFilters] = useState<SelectedUI[] | null>(
    null,
  );
  const { params, actions } = useListQueryParams();

  const loadProfessors = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getProfessorsV2({
        ...params,
        language: language,
        include_filters: true,
      });
      setProfessors(res.data.cards);
      setFilters(mapBackendFilters(res.data.filters));
      setSelectedFilters(mapBackendSelected(res.data.filters.selected));
      setPagination({
        total: res.data.total,
        total_pages: res.data.total_pages,
        page: res.data.page,
        size: res.data.size,
      });
      setIsFirstLoad(false);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfessors();
  }, [params, language]);

  return (
    <div lang={language.toLowerCase()} className={s.professors}>
      <DetailHeader
        showBackButton={false}
        title={"professor.professors.title"}
      />
      <ListController
        filtersSlot={
          filters && (
            <FiltersPanel
              loading={loading}
              totalItems={pagination?.total ? pagination.total : 0}
              actions={actions}
              searchPlaceholder={`professors.search`}
              filtersData={filters}
              selectedFilters={selectedFilters}
              params={params}
            />
          )
        }
        paginationSlot={
          pagination && (
            <Pagination
              onPageChange={(p) => actions.set({ page: p })}
              onSizeChange={(s) => actions.set({ size: s })}
              pagination={{
                page: params.page,
                size: params.size,
                total: pagination.total,
                total_pages: pagination.total_pages,
              }}
            />
          )
        }
      >
        {loading ? (
          <ProfessorCardSkeletons amount={Number(params.size)} />
        ) : (
          <ProfessorsList professors={professors} loading={loading} />
        )}
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
