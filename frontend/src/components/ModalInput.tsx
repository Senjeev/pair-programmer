// src/components/ModalInput.tsx
import React, { useState } from "react";
import "../App.css";


interface ModalInputProps {
  title: string;
  placeholder?: string;
  onSubmit: (value: string) => void;
  onClose?: () => void;
}

const ModalInput: React.FC<ModalInputProps> = ({ title, placeholder = "", onSubmit, onClose }) => {
  const [value, setValue] = useState("");

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal-card">
        <h3>{title}</h3>
        <input
          className="input"
          placeholder={placeholder}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSubmit(value);
            if (e.key === "Escape" && onClose) onClose();
          }}
          autoFocus
        />
        <div className="modal-actions">
          <button className="btn btn-primary" onClick={() => onSubmit(value)}>
            Submit
          </button>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalInput;
