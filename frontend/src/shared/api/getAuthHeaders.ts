import { LS_TOKEN_KEY } from "@/shared/common/helpers/commonConstants.ts";

export const getAuthHeaders = () => {
  const accessToken = localStorage.getItem(LS_TOKEN_KEY);

  if (!accessToken) {
    throw new Error("No access token found");
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
};
