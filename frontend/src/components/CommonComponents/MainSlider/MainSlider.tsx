import UniversalSlider from "../../ui/UniversalSlider/UniversalSlider";
import Slide from "./Slide/Slide";
import { useEffect, useState } from "react";

// slides,
// autoplay = false,
// loop = true,
// pagination = true,
// navigation,
// paginationType = "story",
// slidesPerView = 1,
// effect = "slide",
// navigationPosition = "center",
// delay = 5000,
// className = "",
// isFullWidth = false,

const MainSlider: React.FC = () => {
  const [screenWidth, setScreenWidth] = useState(window.innerWidth);
  const TABLET_BREAKPOINT = 768;
  const slidesInfo = [
    {
      name: "Occlusion, TMJ Dysfunctions And Orofacial Pain From А To Z. The Most Comprehensive Lecture Course",
      type: "Online course",
      newPrice: "15",
      oldPrice: "500",
      lessonsCount: "10 modules: 8 lessons + PDF materials",
      description:
        "Lorem ipsum dolor sit amet consectetur. Id ut in praesent eu velit integer praesent suspendisse egestas. Enim egestas pellentesque leo.",
      authors: ["Bill Dischinger", "Alfredo Rizzo", "Trevor Nichols"],
      photo:
        "https://dent-s.com/assets/img/preview_img/All About Torques In Orthodontics.png",
      slug: "",
    },
    {
      name: "Occlusion, TMJ Dysfunctions And Orofacial Pain From А To Z. The Most Comprehensive Lecture Course",
      type: "Online course",
      newPrice: "15",
      oldPrice: "500",
      lessonsCount: "10 modules: 8 lessons + PDF materials",
      description:
        "Lorem ipsum dolor sit amet consectetur. Id ut in praesent eu velit integer praesent suspendisse egestas. Enim egestas pellentesque leo.",
      authors: ["Bill Dischinger", "Alfredo Rizzo", "Trevor Nichols"],
      photo:
        "https://dent-s.com/assets/img/preview_img/All About Torques In Orthodontics.png",
      slug: "",
    },
    {
      name: "Occlusion, TMJ Dysfunctions And Orofacial Pain From А To Z. The Most Comprehensive Lecture Course",
      type: "Online course",
      newPrice: "15",
      oldPrice: "500",
      lessonsCount: "10 modules: 8 lessons + PDF materials",
      description:
        "Lorem ipsum dolor sit amet consectetur. Id ut in praesent eu velit integer praesent suspendisse egestas. Enim egestas pellentesque leo.",
      authors: ["Bill Dischinger", "Alfredo Rizzo", "Trevor Nichols"],
      photo:
        "https://dent-s.com/assets/img/preview_img/All About Torques In Orthodontics.png",
      slug: "",
    },
    {
      name: "Occlusion, TMJ Dysfunctions And Orofacial Pain From А To Z. The Most Comprehensive Lecture Course",
      type: "Online course",
      newPrice: "15",
      oldPrice: "500",
      lessonsCount: "10 modules: 8 lessons + PDF materials",
      description:
        "Lorem ipsum dolor sit amet consectetur. Id ut in praesent eu velit integer praesent suspendisse egestas. Enim egestas pellentesque leo.",
      authors: ["Bill Dischinger", "Alfredo Rizzo", "Trevor Nichols"],
      photo:
        "https://dent-s.com/assets/img/preview_img/All About Torques In Orthodontics.png",
      slug: "",
    },
    {
      name: "Occlusion, TMJ Dysfunctions And Orofacial Pain From А To Z. The Most Comprehensive Lecture Course",
      type: "Online course",
      newPrice: "15",
      oldPrice: "500",
      lessonsCount: "10 modules: 8 lessons + PDF materials",
      description:
        "Lorem ipsum dolor sit amet consectetur. Id ut in praesent eu velit integer praesent suspendisse egestas. Enim egestas pellentesque leo.",
      authors: ["Bill Dischinger", "Alfredo Rizzo", "Trevor Nichols"],
      photo:
        "https://dent-s.com/assets/img/preview_img/All About Torques In Orthodontics.png",
      slug: "",
    },
  ];

  useEffect(() => {
    const handleScreenResize = () => {
      setScreenWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleScreenResize);

    handleScreenResize();

    return () => {
      window.removeEventListener("resize", handleScreenResize);
    };
  }, [screenWidth]);

  const slides = slidesInfo.map((slideInfo: (typeof slidesInfo)[number]) => (
    <Slide slideInfo={slideInfo} />
  ));
  return (
    <UniversalSlider
      autoplay
      slides={slides}
      navigation
      navigationPosition="top-right"
      zoneNavigation={screenWidth < TABLET_BREAKPOINT}
      paginationPosition="top"
      theme="hero"
    />
  );
};

export default MainSlider;
