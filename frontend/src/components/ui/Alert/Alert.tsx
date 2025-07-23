import Swal from "sweetalert2";
import withReactContent from "sweetalert2-react-content";
import "./Alert.scss";
import { ReactElement } from "react";

export const Alert = (
  title: string,
  icon?: ReactElement,
  onClose?: () => void,
) => {
  withReactContent(Swal)
    .fire({
      title: (
        <div className="custom_swal_title_container">
          {icon && <div className="alert_icon">{icon}</div>}
          {title}
        </div>
      ),
      customClass: {
        container: "custom_swal_container",
        popup: "custom_swal_popup",
        title: "custom_swal_title",
        confirmButton: "custom_swal_button",
      },
    })
    .then(() => {
      if (onClose) {
        onClose();
      }
    });
};
