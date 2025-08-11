import { useState } from "react";
import MultiSelect from "../../../../../components/CommonComponents/MultiSelect/MultiSelect";
import s from "./SlideItem.module.scss";
import { ArrowX, BackArrow } from "../../../../../assets/icons";
import Input from "../../../../../components/ui/Inputs/Input/Input";

interface SlideItemProps {
  slide: any;
  landingOptions: any[];
  onLandingChange: (
    id: number,
    newLanding: { name: string; value: string | string[] }
  ) => void;
  onTypeChange: (id: number, newType: string) => void;
  handleInputKeyDown: (
    id: number,
    e: React.KeyboardEvent<HTMLInputElement>
  ) => void;
  handleDeleteItem: (id: number) => void;
  handleMoveToTop: (orderIndex: number) => void;
  handleMoveToBottom: (orderIndex: number) => void;
}

const SlideType = {
  free: "FREE",
  course: "COURSE",
} as const;

const SlideItem = ({
  slide,
  landingOptions,
  onLandingChange,
  handleInputKeyDown,
  onTypeChange,
  handleDeleteItem,
  handleMoveToTop,
  handleMoveToBottom,
}: SlideItemProps) => {
  const slideTypeOptions = Object.entries(SlideType).map(([name, value]) => ({
    name: name.toUpperCase(),
    value,
  }));
  const commonFilterProps = {
    isSearchable: false,
    placeholder: "",
    isMultiple: false,
    valueKey: "value" as const,
    labelKey: "name" as const,
  };
  console.log(slide.order_index);
  return (
    <li className={s.slide}>
      <div className={s.slide_content}>
        <div className={s.slide_arrows}>
          <button
            onClick={() => handleMoveToTop(slide.order_index)}
            className={s.top_arrow}
          >
            <BackArrow />
          </button>
          <button
            onClick={() => handleMoveToBottom(slide.order_index)}
            className={s.bottom_arrow}
          >
            <BackArrow />
          </button>
        </div>
        <div className={s.slide_info}>
          <span>{slide.type}</span>
          <div>
            {slide.title || slide.landing?.landing_name || "No landing name"}
          </div>
        </div>
        {landingOptions.length > 0 && (
          <div className={s.filters}>
            {slide.type === SlideType.course ? (
              <MultiSelect
                {...commonFilterProps}
                placeholder="Landings"
                options={landingOptions}
                id={slide.landing?.landing_name}
                selectedValue={slide.landing?.id}
                onChange={(e) => {
                  const selectedLanding = landingOptions.find(
                    (opt) => opt.value === e.value
                  );
                  if (selectedLanding) {
                    onLandingChange(slide.id, {
                      name: selectedLanding.name,
                      value: selectedLanding.value,
                    });
                  }
                }}
              />
            ) : (
              <Input
                className={s.title_input}
                defaultValue={slide.title || ""}
                placeholder="Landing name"
                onKeyDown={(e) => handleInputKeyDown(slide.id, e)}
              />
            )}
            <MultiSelect
              {...commonFilterProps}
              options={slideTypeOptions}
              id="type-select"
              selectedValue={slide.type}
              onChange={(e) => onTypeChange(slide.id, e.value as string)}
            />
          </div>
        )}
        <button onClick={() => handleDeleteItem(slide.id)}>
          <ArrowX />
        </button>
      </div>
    </li>
  );
};

export default SlideItem;
