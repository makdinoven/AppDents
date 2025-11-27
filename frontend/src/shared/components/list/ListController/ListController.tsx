import s from "./ListController.module.scss";
import Pagination, { PaginationType } from "../Pagination/Pagination.tsx";
import { useEffect } from "react";
import { Trans } from "react-i18next";
import { BookCardsParams } from "../../../api/mainApi/types.ts";
import { useListQueryParams } from "../model/useListQueryParams.ts";
import { LanguagesType } from "../../ui/LangLogo/LangLogo.tsx";
import FiltersPanel from "../../filters/FiltersPanel/FiltersPanel.tsx";
import { FiltersData } from "../../filters/types.ts";

type ListControllerProps = {
  type: string;
  size?: number;
  loadData: (params: BookCardsParams) => void;
  language?: string;
  children: React.ReactNode;
  SkeletonComponent?: React.ComponentType<
    { amount: number } & Record<string, any>
  >;
  skeletonProps?: Record<string, any>;
  loading?: boolean;
  pagination: PaginationType | null;
  filtersData: FiltersData;
};

const ListController = ({
  type,
  loadData,
  children,
  language,
  size = 12,
  SkeletonComponent,
  skeletonProps,
  loading,
  pagination,
  filtersData,
}: ListControllerProps) => {
  const { params, setParams } = useListQueryParams({
    defaultPage: 1,
    defaultPageSize: size ?? 12,
  });

  useEffect(() => {
    loadData({
      page: params.page,
      size: params.pageSize,
      language: language as LanguagesType,
      ...params.filters,
    });
  }, [params, language]);

  return (
    <div className={s.list_controller_container}>
      <div>
        <FiltersPanel
          searchKey={"search"}
          searchPlaceholder={`${type}.search`}
          filtersData={filtersData}
          params={params}
          setParams={setParams}
        />

        <p
          className={`${s.results_found} ${pagination?.total ? s.loaded : ""}`}
        >
          <Trans
            i18nKey={`${type}.found`}
            values={{ count: pagination?.total ?? 0 }}
          />
        </p>
      </div>

      {loading && SkeletonComponent ? (
        <SkeletonComponent
          amount={params?.pageSize ? Number(params?.pageSize) : size}
          {...skeletonProps}
        />
      ) : (
        children
      )}

      {pagination && (
        <Pagination
          onPageChange={(p) => setParams({ page: p })}
          onSizeChange={(s) => setParams({ pageSize: s })}
          pagination={{
            ...pagination,
            page: params.page,
            size: params.pageSize,
          }}
        />
      )}
    </div>
  );
};

export default ListController;
