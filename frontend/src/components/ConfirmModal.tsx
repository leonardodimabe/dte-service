import { type ReactNode } from "react";
import Icon, { type IconName } from "./Icon";
import Modal from "./Modal";

interface Props {
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  confirmIcon?: IconName;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

/** Confirmación para acciones sensibles (eliminar/reactivar). */
export default function ConfirmModal({
  title,
  message,
  confirmLabel = "Confirmar",
  confirmIcon,
  danger,
  busy,
  onConfirm,
  onClose,
}: Props) {
  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="secondary" type="button" onClick={onClose}>
            <Icon name="x" />
            Cancelar
          </button>
          <button
            type="button"
            className={danger ? "danger" : ""}
            disabled={busy}
            onClick={onConfirm}
          >
            {confirmIcon && <Icon name={confirmIcon} />}
            {confirmLabel}
          </button>
        </>
      }
    >
      <p style={{ margin: 0 }}>{message}</p>
    </Modal>
  );
}
