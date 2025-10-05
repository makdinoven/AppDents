import PdfReader from "./PdfReader.tsx";
import PdfReaderFullScreen from "./PdfReaderFullScreen.tsx";
import { useSearchParams } from "react-router-dom";
import { useState } from "react";

interface PdfReaderWrapperProps {
  parentId: string;
  url: string;
  isSlideActive: boolean;
}

export const PDF_READER_FULLSCREEN_KEY = "reader_fullscreen";

const PdfReaderWrapper = ({
  parentId,
  url,
  isSlideActive,
}: PdfReaderWrapperProps) => {
  const [currentPage, setCurrentPage] = useState<string>("1");
  const [searchParams, setSearchParams] = useSearchParams();
  const openFullScreen = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(PDF_READER_FULLSCREEN_KEY, "");
    setSearchParams(newParams, { replace: true });
  };

  return (
    isSlideActive && (
      <>
        <PdfReaderFullScreen
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
          parentId={parentId}
          url={url}
        />

        <PdfReader
          currentPage={currentPage}
          setCurrentPage={setCurrentPage}
          url={url}
          fullScreen={false}
          setFullScreen={openFullScreen}
        />
      </>
    )
  );
};
export default PdfReaderWrapper;
