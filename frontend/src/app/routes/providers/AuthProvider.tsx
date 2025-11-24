import { ReactNode, useEffect } from "react";
import { AppDispatchType } from "../../../shared/store/store.ts";
import { useDispatch, useSelector } from "react-redux";
import { setLanguage } from "../../../shared/store/slices/userSlice.ts";
import { getMe } from "../../../shared/store/actions/userActions.ts";
import { getCart } from "../../../shared/store/actions/cartActions.ts";
import {
  LS_LANGUAGE_KEY,
  REF_CODE_LS_KEY,
  REF_CODE_PARAM,
} from "../../../shared/common/helpers/commonConstants.ts";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const dispatch = useDispatch<AppDispatchType>();
  const language = useSelector((state: any) => state.user.language);
  const isLogged = useSelector((state: any) => state.user.isLogged);

  useEffect(() => {
    dispatch(getMe());
    const storedLanguage = localStorage.getItem(LS_LANGUAGE_KEY) || language;
    dispatch(setLanguage(storedLanguage));
  }, []);

  useEffect(() => {
    if (isLogged) {
      dispatch(getCart());
    } else {
      const searchParams = new URLSearchParams(location.search);
      const rcCode = searchParams.get(REF_CODE_PARAM);

      if (rcCode) {
        localStorage.setItem(REF_CODE_LS_KEY, rcCode);
      }
    }
  }, [isLogged]);

  return <div lang={language.toLowerCase()}>{children}</div>;
};
