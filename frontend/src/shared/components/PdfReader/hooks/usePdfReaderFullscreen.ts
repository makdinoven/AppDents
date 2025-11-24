import { useSearchParams } from "react-router-dom";
import {
  PDF_READER_FULLSCREEN_KEY,
  PDF_READER_SCALE_KEY,
} from "../constants.ts";

export const usePdfReaderFullscreen = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const fullScreen = searchParams.has(PDF_READER_FULLSCREEN_KEY);
  const toggleFullScreen = (state: boolean) => {
    const newParams = new URLSearchParams(searchParams);
    if (state) {
      newParams.set(PDF_READER_FULLSCREEN_KEY, "");
    } else {
      newParams.delete(PDF_READER_FULLSCREEN_KEY);
      newParams.delete(PDF_READER_SCALE_KEY);
    }
    setSearchParams(newParams, { replace: true });
  };

  const handleCloseFullScreen = () => {
    toggleFullScreen(false);
  };

  const handleOpenFullScreen = () => {
    toggleFullScreen(true);
  };

  return {
    fullScreen,
    toggleFullScreen,
    handleCloseFullScreen,
    handleOpenFullScreen,
  };
};
