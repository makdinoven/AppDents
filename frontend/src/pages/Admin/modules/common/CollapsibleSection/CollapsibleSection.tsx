import s from "./CollapsibleSection.module.scss";
import AdminField from "../AdminField/AdminField.tsx";
import PrettyButton from "../../../../../components/ui/PrettyButton/PrettyButton.tsx";
import { t } from "i18next";
import { Trans } from "react-i18next";

const CollapsibleSection = ({
  title,
  data,
  fields,
  isOpen,
  toggleOpen,
  handleDelete,
  onChange,
  children,
}: {
  title: string;
  data: any;
  fields: any;
  isOpen: boolean;
  toggleOpen: () => void;
  handleDelete: () => void;
  onChange: any;
  children?: React.ReactNode;
}) => {
  return (
    <>
      {!isOpen ? (
        <div className={s.section_closed}>
          <div className={s.section_name}>
            <Trans i18nKey={`${title}.one`} /> {data.id && data.id}
            <span>{data.name}</span>
          </div>
          <PrettyButton text={t("open")} onClick={toggleOpen} />
        </div>
      ) : (
        <div className={s.section}>
          <div className={s.section_header}>
            <PrettyButton
              variant="danger"
              text={t(`${title}.delete`)}
              onClick={handleDelete}
            />
            <PrettyButton text={t(`${title}.close`)} onClick={toggleOpen} />
          </div>

          {fields.map(
            ({
              id,
              label,
              placeholder,
              type = "input",
              inputType,
            }: {
              id: string;
              label: string;
              placeholder: string;
              type?: "input" | "textarea";
              inputType?: string;
            }) => (
              <AdminField
                key={id}
                type={type}
                inputType={inputType}
                id={id}
                label={t(`${title}.${label}`)}
                placeholder={t(`${title}.${placeholder}`)}
                value={data[id]}
                onChange={onChange}
              />
            ),
          )}

          {children}
        </div>
      )}
    </>
  );
};

export default CollapsibleSection;
