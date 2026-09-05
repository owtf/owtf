import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Button } from "./shared";

// A non-modal companion to the workspace: navigation remains usable.
export default function Inspector({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const heading = useId();
  const [expanded, setExpanded] = useState(false);
  const close = useRef<HTMLButtonElement>(null);
  const dismiss = useRef(onClose);
  dismiss.current = onClose;
  useEffect(() => {
    const previous = document.activeElement;
    close.current?.focus();
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !document.querySelector('[role="dialog"]'))
        dismiss.current();
    };
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("keydown", escape);
      if (previous instanceof HTMLElement && previous.isConnected)
        previous.focus();
    };
  }, []);
  return createPortal(
    <aside
      className="workspace-inspector"
      data-expanded={expanded}
      aria-labelledby={heading}
    >
      <header>
        <h2 id={heading}>{title}</h2>
        <Button
          variant="outline"
          size="sm"
          aria-label={`Expand ${title}`}
          aria-pressed={expanded}
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Restore" : "Expand"}
        </Button>
        <Button
          ref={close}
          variant="ghost"
          size="sm"
          onClick={onClose}
          aria-label={`Close ${title}`}
        >
          Close
        </Button>
      </header>
      <div className="inspector-content">{children}</div>
    </aside>,
    document.body,
  );
}
