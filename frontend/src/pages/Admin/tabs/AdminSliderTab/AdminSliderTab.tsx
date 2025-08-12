import { useEffect, useState } from "react";
import PrettyButton from "../../../../components/ui/PrettyButton/PrettyButton";
import { useSearchParams } from "react-router-dom";
import {
  LANGUAGES_NAME,
  FILTER_PARAM_KEYS,
} from "../../../../common/helpers/commonConstants";
import MultiSelect from "../../../../components/CommonComponents/MultiSelect/MultiSelect";
import s from "./AdminSliderTab.module.scss";
import { adminApi } from "../../../../api/adminApi/adminApi";
import { ParamsType } from "../../../../api/adminApi/types";
import SlideItem from "./SlideItem/SlideItem.tsx";
import LoaderOverlay from "../../../../components/ui/LoaderOverlay/LoaderOverlay";
import Loader from "../../../../components/ui/Loader/Loader";

const SlideType = {
  free: "FREE",
  course: "COURSE",
} as const;

type OptionType = {
  name: string;
  value: string | number | string[];
};

const AdminSliderTab = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedLang, setSelectedLang] = useState<string>("all");
  const [slides, setSlides] = useState<any[]>([]);
  const [landings, setLandings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const tab = searchParams.get("tab");

  useEffect(() => {
    setSelectedLang(searchParams.get(FILTER_PARAM_KEYS.language) || "EN");
  }, [searchParams]);

  useEffect(() => {
    const language = searchParams.get(FILTER_PARAM_KEYS.language) || "EN";

    loadSlidesData(language);
    loadLandingsData({ language, size: 10000 });
  }, [searchParams]);

  const loadSlidesData = async (language: string) => {
    try {
      setLoading(true);
      if (language) {
        const res = await adminApi.getSlides(language);
        setSlides(res.data.slides);
      }
    } catch (error) {
      console.log("Slides loading error:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadLandingsData = async (params: ParamsType) => {
    try {
      setLoading(true);
      if (params) {
        const res = await adminApi.getLandingsList(params);
        const landings: OptionType[] = res.data.items.map((item: any) => ({
          name: item.landing_name,
          value: item.id,
        }));

        setLandings(landings);
      }
    } catch (error) {
      console.log("Landings loading error:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSlide = () => {
    const newSlide: any = {
      id: Date.now(),
      type: SlideType.course,
    };

    setSlides((prevSlides) => [
      ...prevSlides,
      { ...newSlide, order_index: prevSlides.length + 1 },
    ]);
  };

  const handleDeleteSlide = (id: number) => {
    setSlides((prevSlides) => prevSlides.filter((slide) => slide.id !== id));
  };

  const updateParam = (paramKey: string, value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value === "all") {
      newParams.delete(paramKey);
    } else {
      newParams.set(paramKey, String(value));
    }
    setSearchParams(newParams, { replace: true });
  };

  const handleLanguageChange = (e: OptionType) => {
    updateParam(FILTER_PARAM_KEYS.language, e.value as string);
  };

  const handleTypeChange = (id: number, newType: string) => {
    setSlides((prevSlides) => {
      if (!prevSlides) return prevSlides;
      return prevSlides.map((slide) =>
        slide.id === id ? { ...slide, type: newType } : slide
      );
    });
  };

  const handleInputKeyDown = (
    id: number,
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (e.key === "Enter") {
      const newValue = e.currentTarget.value;
      setSlides((prevSlides) => {
        if (!prevSlides) return prevSlides;
        return prevSlides.map((slide) =>
          slide.id === id ? { ...slide, title: newValue } : slide
        );
      });
    }
  };

  const handleLandingChange = (id: number, newLanding: any) => {
    setSlides((prevSlides) => {
      if (!prevSlides) return prevSlides;
      return prevSlides.map((slide) =>
        slide.id === id
          ? {
              ...slide,
              landing: {
                id: newLanding.value,
                landing_name: newLanding.name,
              },
            }
          : slide
      );
    });
  };

  const handleSaveChanges = async (language: string, slides: any[]) => {
    try {
      setLoading(true);
      const data = slides.map((slide) =>
        slide.type === SlideType.free
          ? {
              id: slide.id || 0,
              type: slide.type,
              order_index: slide.order_index || 0,
              bg_media_url: slide.bg_media_url || "",
              bg_video_url: slide.bg_video_url || "",
              title: slide.title || "",
              description: slide.description || "",
              target_url: slide.target_url || "",
            }
          : {
              id: slide.id,
              type: slide.type,
              order_index: slide.order_index,
              landing_id: slide.landing.id,
              landing_slug: slide.landing.slug,
            }
      );

      await adminApi.saveSlides(language, { slides: data });
    } catch (error) {
      console.error("Error updating slides:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleMoveToTop = (orderIndex: number) => {
    setSlides((prevSlides) => {
      const newSlides = [...prevSlides];

      const currentIndex = newSlides.findIndex(
        (slide) => slide.order_index === orderIndex
      );

      if (currentIndex <= 0) return newSlides;

      [newSlides[currentIndex - 1], newSlides[currentIndex]] = [
        newSlides[currentIndex],
        newSlides[currentIndex - 1],
      ];

      return newSlides.map((slide, index) => ({
        ...slide,
        order_index: index + 1,
      }));
    });
  };

  const handleMoveToBottom = (orderIndex: number) => {
    setSlides((prevSlides) => {
      const newSlides = [...prevSlides];

      const currentIndex = newSlides.findIndex(
        (slide) => slide.order_index === orderIndex
      );

      if (currentIndex === newSlides.length - 1) return newSlides;

      [newSlides[currentIndex], newSlides[currentIndex + 1]] = [
        newSlides[currentIndex + 1],
        newSlides[currentIndex],
      ];

      return newSlides.map((slide, index) => ({
        ...slide,
        order_index: index + 1,
      }));
    });
  };
  return (
    <div className={s.slider_tab}>
      <div className={s.slider_tab_header}>
        <PrettyButton
          variant={"primary"}
          text={`admin.${tab}.save`}
          onClick={() => handleSaveChanges(selectedLang, slides)}
          className={s.add_slide_button}
        />
        <PrettyButton
          variant={"primary"}
          text={`admin.${tab}.create`}
          onClick={handleAddSlide}
          className={s.add_slide_button}
        />
        <div className={s.slider_tab_select}>
          <MultiSelect
            isSearchable={false}
            placeholder=""
            isMultiple={false}
            valueKey="value"
            labelKey="name"
            options={LANGUAGES_NAME}
            id={FILTER_PARAM_KEYS.language}
            selectedValue={selectedLang}
            onChange={handleLanguageChange}
          />
        </div>
      </div>
      <ul className={s.slides_list}>
        {loading && (
          <>
            <LoaderOverlay />
          </>
        )}
        {slides.length > 0 ? (
          slides.map((slide) => {
            return (
              <SlideItem
                key={slide.id}
                slide={slide}
                onLandingChange={handleLandingChange}
                onTypeChange={handleTypeChange}
                handleInputKeyDown={handleInputKeyDown}
                handleDeleteItem={handleDeleteSlide}
                landingOptions={landings}
                handleMoveToTop={handleMoveToTop}
                handleMoveToBottom={handleMoveToBottom}
              />
            );
          })
        ) : (
          <Loader />
        )}
      </ul>
    </div>
  );
};

export default AdminSliderTab;
