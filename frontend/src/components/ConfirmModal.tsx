import React from "react";
import "../App.css";

interface ConfirmModalProps {
  title?: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

const ConfirmModal: React.FC<ConfirmModalProps> = ({
  title = "Confirm",
  message,
  onConfirm,
  onCancel,
}) => {
  return (
    <div className="confirm-overlay" role="dialog" aria-modal="true">
      <div className="confirm-box">
        <h3>{title}</h3>
        <p>{message}</p>

        <div className="confirm-actions">
          <button className="btn btn-primary" onClick={onConfirm}>
            Yes
          </button>
          <button className="btn btn-secondary" onClick={onCancel}>
            No
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
