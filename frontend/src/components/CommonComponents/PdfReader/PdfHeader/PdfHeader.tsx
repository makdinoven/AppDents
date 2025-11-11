import s from "./PdfHeader.module.scss";
import {
  Chevron,
  ListIcon,
  MaximizeIcon,
  ModalClose,
  ZoomIn,
  ZoomOut,
} from "../../../../assets/icons";
import { t } from "i18next";
import { scales, screenResolutionMap } from "../constants.ts";
import MultiSelect from "../../MultiSelect/MultiSelect.tsx";

type Props = {
  handleThumbNailsClick: () => void;
  totalPages?: number;
  currentPage: string;
  handleInputChange: (val: string) => void;
  handleZoom: (val: "in" | "out") => void;
  screenWidth: number;
  handleSelectChange: (val: {
    value: number | string | string[];
    name: string;
  }) => void;
  goToPrevPage: () => void;
  goToNextPage: () => void;
  handleCloseFullScreen: (() => void) | null;
  handleOpenFullScreen: () => void;
  fullScreen: boolean;
  scale: number;
};

const PdfHeader = ({
  handleThumbNailsClick,
  totalPages,
  currentPage,
  handleInputChange,
  handleZoom,
  screenWidth,
  handleSelectChange,
  goToPrevPage,
  goToNextPage,
  handleCloseFullScreen,
  handleOpenFullScreen,
  fullScreen,
  scale,
}: Props) => {
  const findScale = scales.find((option) => option.value === scale);

  const isFirstPage = Number(currentPage) === 1 || !totalPages;
  const isLastPage = Number(currentPage) === Number(totalPages) || !totalPages;
  const isFirstScale = scale === scales[0].value;
  const isLastScale = scale === scales[scales.length - 1].value;

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
              value={currentPage === "" ? "" : currentPage}
              onChange={(e) => handleInputChange(e.target.value)}
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
                onChange={(val) => handleSelectChange(val)}
                centrate
              />
            )}
          </div>
          <button
            className={`${s.expand_button} ${s.close_icon}`}
            onClick={handleCloseFullScreen ? handleCloseFullScreen : undefined}
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
          {renderScalesButtons}
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
