import {
  AppDispatchType,
  AppRootStateType,
} from "../../../../shared/store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import { adminApi } from "../../../../shared/api/adminApi/adminApi.ts";
import { toggleBookLandingVisibility } from "../../../../shared/store/slices/adminSlice.ts";
import { generateId } from "../../../../shared/common/helpers/helpers.ts";
import {
  createBookLanding,
  getBookLandings,
  searchBookLandings,
} from "../../../../shared/store/actions/adminActions.ts";
import AdminList from "../modules/common/AdminList/AdminList.tsx";
import { PATHS } from "../../../../app/routes/routes.ts";

const INITIAL_BOOK_LANDING = {
  landing_name: `New book landing ${generateId()}`,
  is_hidden: true,
  page_name: `book-${generateId()}`,
};

const AdminBookLandingsListing = () => {
  const loading = useSelector((state: AppRootStateType) => state.admin.loading);
  const bookLandings = useSelector(
    (state: AppRootStateType) => state.admin.bookLandings,
  );
  const dispatch = useDispatch<AppDispatchType>();

  const handleToggleBookVisibility = (id: number, isHidden: boolean) => {
    try {
      adminApi.toggleBookLandingVisibility(id, isHidden);
      dispatch(toggleBookLandingVisibility({ id, isHidden }));
    } catch (error) {
      dispatch(toggleBookLandingVisibility({ id, isHidden: !isHidden }));
      console.log(error);
    }
  };

  return (
    <>
      <AdminList<any>
        transKey={"bookLandings"}
        data={bookLandings}
        itemName={"landing_name"}
        itemLink={(book) => PATHS.ADMIN_BOOK_LANDING_DETAIL.build(book.id)}
        loading={loading}
        onSearch={(params) => dispatch(searchBookLandings(params))}
        onLoad={(params) => dispatch(getBookLandings(params))}
        onCreate={() => dispatch(createBookLanding(INITIAL_BOOK_LANDING))}
        showToggle={true}
        showLanguageFilter={true}
        handleToggle={(id: number, isHidden: boolean) =>
          handleToggleBookVisibility(id, isHidden)
        }
      />
    </>
  );
};

export default AdminBookLandingsListing;
