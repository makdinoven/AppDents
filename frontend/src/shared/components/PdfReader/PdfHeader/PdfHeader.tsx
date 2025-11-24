import s from "./PdfHeader.module.scss";
import {
  Chevron,
  ListIcon,
  MaximizeIcon,
  ModalClose,
  ZoomIn,
  ZoomOut,
} from "../../../assets/icons";
import { t } from "i18next";
import { scales, screenResolutionMap } from "../constants.ts";
import MultiSelect from "../../MultiSelect/MultiSelect.tsx";
import { useScreenWidth } from "../../../common/hooks/useScreenWidth.ts";
import { useEffect, useState } from "react";
import { usePdfReaderFullscreen } from "../hooks/usePdfReaderFullscreen.ts";
import { usePdfReaderScale } from "../hooks/usePdfReaderScale.ts";

type Props = {
  handleThumbNailsClick: () => void;
  totalPages?: number;
  currentPage: string;
  handleScrollToPage: (p: number) => void;
};

const PdfHeader = ({
  handleThumbNailsClick,
  totalPages,
  currentPage,
  handleScrollToPage,
}: Props) => {
  const [isInputFocused, setIsInputFocused] = useState(false);
  const { scale, handleZoom, handleScaleSelectChange } = usePdfReaderScale();
  const [inputValue, setInputValue] = useState(currentPage);
  const findScale = scales.find((option) => option.value === scale);
  const screenWidth = useScreenWidth();
  const isFirstPage = Number(currentPage) === 1 || !totalPages;
  const isLastPage = Number(currentPage) === Number(totalPages) || !totalPages;
  const isFirstScale = scale === scales[0].value || !totalPages;
  const isLastScale = scale === scales[scales.length - 1].value || !totalPages;
  const pageNum = Number(currentPage);
  const { fullScreen, handleOpenFullScreen, handleCloseFullScreen } =
    usePdfReaderFullscreen();

  const goToPrevPage = () => {
    const newPage = Math.max(1, pageNum - 1);
    handleScrollToPage(newPage);
  };

  const goToNextPage = () => {
    const newPage = Math.min(totalPages || 1, pageNum + 1);
    handleScrollToPage(newPage);
  };

  const handleInputSubmit = () => {
    let page = Number(inputValue);
    if (isNaN(page)) return;

    if (page < 1) page = 1;
    if (totalPages && page > totalPages) page = totalPages;
    handleScrollToPage(page);
  };

  const renderNextPrevButtons = (
    <div className={s.arrows_wrapper}>
      <button
        onClick={goToPrevPage}
        className={`${s.up} ${isFirstPage ? s.inactive : ""}`}
      >
        <Chevron />
      </button>
      <button
        onClick={goToNextPage}
        className={`${s.down} ${isLastPage ? s.inactive : ""}`}
      >
        <Chevron />
      </button>
    </div>
  );

  const renderScalesButtons = (
    <div className={s.scales_wrapper}>
      <button
        className={`${isFirstScale ? s.inactive : ""}`}
        onClick={() => handleZoom("out")}
      >
        <ZoomOut />
      </button>
      <button
        className={`${isLastScale ? s.inactive : ""}`}
        onClick={() => handleZoom("in")}
      >
        <ZoomIn />
      </button>
    </div>
  );

  useEffect(() => {
    if (!isInputFocused) {
      setInputValue(currentPage);
    }
  }, [currentPage]);

  const headerContent = new Map([
    [
      true,
      <>
        <div className={s.left_side}>
          <button className={s.list} onClick={handleThumbNailsClick}>
            <ListIcon />
          </button>
          <div className={`${s.page_indicator} ${s.full_screen}`}>
            <input
              type={"number"}
              min={1}
              max={totalPages || 1}
              className={s.page_input}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onFocus={() => setIsInputFocused(true)}
              onBlur={() => setIsInputFocused(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleInputSubmit();
                }
              }}
            />
            {t("of")}
            <span>{totalPages ? totalPages : 0}</span>
          </div>
          {screenWidth > screenResolutionMap.get("mobile")!.width &&
            renderNextPrevButtons}
        </div>
        <div className={s.right_side}>
          {renderScalesButtons}
          <div className={s.scales_wrapper}>
            {screenWidth > screenResolutionMap.get("mobile")!.width && (
              <MultiSelect
                isSearchable={false}
                isMultiple={false}
                valueKey={"value" as const}
                labelKey={"label" as const}
                id={"scales-select"}
                placeholder={scale.toString()}
                options={scales}
                selectedValue={findScale?.value as number}
                onChange={(val) => handleScaleSelectChange(val)}
                centrate
              />
            )}
          </div>
          <button
            className={`${s.expand_button} ${s.close_icon}`}
            onClick={handleCloseFullScreen}
          >
            <ModalClose />
          </button>
        </div>
      </>,
    ],
    [
      false,
      <>
        <div className={s.left_side}>
          {renderNextPrevButtons}
          <p className={s.page_indicator}>
            <span>
              {totalPages ? currentPage : 0}/{totalPages ? totalPages : 0}
            </span>
          </p>
        </div>
        <div className={s.right_side}>
          {/*{renderScalesButtons}*/}
          <button
            className={s.expand_button}
            onClick={handleOpenFullScreen}
            disabled={!totalPages}
          >
            <MaximizeIcon />
          </button>
        </div>
      </>,
    ],
  ]);

  return <div className={s.header}>{headerContent.get(fullScreen)}</div>;
};

export default PdfHeader;
