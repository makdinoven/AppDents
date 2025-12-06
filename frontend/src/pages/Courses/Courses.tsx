import s from "./Courses.module.scss";
import { useSelector } from "react-redux";
import { AppRootStateType } from "../../shared/store/store.ts";
import { useEffect, useState } from "react";
import DetailHeader from "../Admin/pages/modules/common/DetailHeader/DetailHeader.tsx";
import ListController from "../../shared/components/list/ListController/ListController.tsx";
import CardsList from "../../shared/components/ProductsSection/CardsList/CardsList.tsx";
import { mainApi } from "../../shared/api/mainApi/mainApi.ts";
import ProductsSection from "../../shared/components/ProductsSection/ProductsSection.tsx";
import CourseCardSkeletons from "../../shared/components/ui/Skeletons/CourseCardSkeletons/CourseCardSkeletons.tsx";
import CustomOrder from "../../shared/components/CustomOrder/CustomOrder.tsx";
import Pagination, {
  PaginationType,
} from "../../shared/components/list/Pagination/Pagination.tsx";
import FiltersPanel from "../../shared/components/filters/FiltersPanel/FiltersPanel.tsx";
import {
  mapBackendFilters,
  mapBackendSelected,
} from "../../shared/components/filters/model/mapBackendFilters.ts";
import {
  FiltersDataUI,
  SelectedUI,
} from "../../shared/components/filters/model/types.ts";
import { useListQueryParams } from "../../shared/components/list/model/useListQueryParams.ts";
import FiltersSkeleton from "../../shared/components/ui/Skeletons/FiltersSkeleton/FiltersSkeleton.tsx";

const Courses = ({ isFree }: { isFree: boolean }) => {
  const { language, isLogged } = useSelector(
    (state: AppRootStateType) => state.user,
  );
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [pagination, setPagination] = useState<PaginationType | null>(null);
  const [filters, setFilters] = useState<FiltersDataUI | null>(null);
  const [selectedFilters, setSelectedFilters] = useState<SelectedUI[] | null>(
    null,
  );
  const { params, actions } = useListQueryParams({
    defaultSort: isLogged ? "recommend" : undefined,
  });

  const loadCourses = async () => {
    setLoading(true);
    try {
      const res = await mainApi.getLandingCardsV2({
        ...params,
        language: language,
        include_filters: true,
      });
      setCourses(res.data.cards);
      setFilters(mapBackendFilters(res.data.filters));
      setSelectedFilters(mapBackendSelected(res.data.filters.selected));
      setPagination({
        total: res.data.total,
        total_pages: res.data.total_pages,
        page: res.data.page,
        size: res.data.size,
      });
    } catch (error) {
      console.log(error);
    } finally {
      setIsFirstLoad(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCourses();
  }, [params, language]);

  useEffect(() => {
    if (params.page !== 1) {
      actions.set({ page: 1 });
    }
  }, [language]);

  return (
    <div lang={language.toLowerCase()} className={s.courses}>
      <DetailHeader title={"courses.title"} />
      <ListController
        filtersSlot={
          !filters && loading ? (
            <FiltersSkeleton />
          ) : (
            <FiltersPanel
              loading={loading}
              totalItems={pagination?.total ? pagination.total : 0}
              actions={actions}
              searchPlaceholder={`courses.search`}
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
        {loading && !selectedFilters ? (
          <CourseCardSkeletons shape amount={Number(params.size)} />
        ) : (
          <CardsList
            showLoaderOverlay={loading}
            loading={loading}
            showSeeMore={false}
            showEndOfList={false}
            cards={courses}
            productCardFlags={{ isFree: isFree, isClient: true }}
            cardType={"course"}
          />
        )}
      </ListController>
      {!isFirstLoad && (
        <>
          <ProductsSection
            showSort={true}
            cardType={"course"}
            productCardFlags={{ isFree: isFree, isOffer: true, isClient: true }}
            sectionTitle={"other.otherCourses"}
            pageSize={4}
          />
          <CustomOrder />
        </>
      )}
    </div>
  );
};

export default Courses;
