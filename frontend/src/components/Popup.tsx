// src/components/Popup.tsx
import React, { useEffect } from "react";
import "../App.css";


interface PopupProps {
  message: string;
  type?: "success" | "error" | "info";
  duration?: number;
  onClose: () => void;
}

const Popup: React.FC<PopupProps> = ({ message, type = "info", duration = 3000, onClose }) => {
  useEffect(() => {
    const timer = window.setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className={`popup popup-${type}`} role="status" aria-live="polite">
      {message}
      <button className="popup-close" onClick={onClose} aria-label="Close popup">
        ×
      </button>
    </div>
  );
};

export default Popup;
