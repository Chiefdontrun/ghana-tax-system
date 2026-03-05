import { useEffect, useRef } from "react";
import clsx from "clsx";
import Button from "./Button";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
  /** If true, clicking backdrop or pressing Esc won't close the modal */
  disableClose?: boolean;
  footer?: React.ReactNode;
}

const sizeMap = {
  sm: "max-w-sm",
  md: "max-w-md",
  lg: "max-w-lg",
  xl: "max-w-2xl",
};

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
  disableClose = false,
  footer,
}: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !disableClose) onClose();
    };
    document.addEventListener("keydown", handleKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = "";
    };
  }, [isOpen, disableClose, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={disableClose ? undefined : onClose}
        aria-hidden
      />
      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "modal-title" : undefined}
        className={clsx(
          "relative bg-white rounded-lg shadow-xl w-full flex flex-col",
          sizeMap[size]
        )}
      >
        {/* Header */}
        {(title || !disableClose) && (
          <div className="flex items-center justify-between px-5 py-4 border-b border-cu-border">
            {title && (
              <h2 id="modal-title" className="text-base font-semibold text-cu-text">
                {title}
              </h2>
            )}
            {!disableClose && (
              <button
                onClick={onClose}
                className="ml-auto text-cu-muted hover:text-cu-text transition-colors"
                aria-label="Close modal"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}
        {/* Body */}
        <div className="p-5 flex-1 overflow-y-auto">{children}</div>
        {/* Footer */}
        {footer && (
          <div className="px-5 py-4 border-t border-cu-border flex justify-end gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

/** Convenience close button for modal footers */
export function ModalCloseButton({ onClose, label = "Close" }: { onClose: () => void; label?: string }) {
  return (
    <Button variant="secondary" size="sm" onClick={onClose}>
      {label}
    </Button>
  );
}
