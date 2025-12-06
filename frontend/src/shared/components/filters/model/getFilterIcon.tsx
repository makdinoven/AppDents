import {
  Book,
  Calendar,
  Dollar,
  EditIcon,
  FileIcon,
  ProfessorsIcon,
  TagIcon,
} from "../../../assets/icons";

export const getFilterIcon = (paramName: string) => {
  if (paramName === "author_ids") return <ProfessorsIcon />;
  if (paramName === "tags") return <TagIcon />;
  if (paramName === "formats") return <FileIcon />;
  if (paramName === "price" || paramName === "price_to") return <Dollar />;
  if (paramName === "year" || paramName === "year_to") return <Calendar />;
  if (paramName === "pages" || paramName === "pages_to") return <Book />;
  if (paramName === "publisher_ids") return <EditIcon />;
  return null;
};
