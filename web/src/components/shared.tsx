import type { ReactNode } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
export { Button };
export function StateBadge({ value }: { value: string }) {
  return (
    <Badge variant="outline" className={`state state-${value}`}>
      {value.replaceAll("_", " ")}
    </Badge>
  );
}
export function ErrorMessage({ error }: { error: unknown }) {
  return error ? (
    <div role="alert" className="error">
      {error instanceof Error ? error.message : String(error)}
    </div>
  ) : null;
}
export function Loading() {
  return (
    <p role="status" className="empty">
      Loading…
    </p>
  );
}
export function PageHead({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="page-head">
      <div>
        <h1>{title}</h1>
        {description && <p className="muted">{description}</p>}
      </div>
      <div className="actions">{children}</div>
    </div>
  );
}
export function SessionLink({
  to,
  children,
  ...rest
}: {
  to: string;
  children: ReactNode;
  className?: string;
}) {
  const [search] = useSearchParams();
  const sep = to.includes("?") ? "&" : "?";
  return (
    <Link
      to={`${to}${search.get("session") ? `${sep}session=${encodeURIComponent(search.get("session")!)}` : ""}`}
      {...rest}
    >
      {children}
    </Link>
  );
}
export function Pager({
  offset,
  total,
  onChange,
  size = 20,
}: {
  offset: number;
  total: number;
  onChange: (offset: number) => void;
  size?: number;
}) {
  return (
    <div className="pager">
      <span>
        {total === 0
          ? "No results"
          : `${offset + 1}–${Math.min(offset + size, total)} of ${total}`}
      </span>
      <div className="actions">
        <Button
          variant="outline"
          size="sm"
          disabled={offset === 0}
          onClick={() => onChange(Math.max(0, offset - size))}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={offset + size >= total}
          onClick={() => onChange(offset + size)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
export function Modal({
  title,
  description,
  open,
  onClose,
  children,
}: {
  title: string;
  description: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}) {
  return (
    <Dialog
      open={open}
      onOpenChange={(value) => {
        if (!value) onClose();
      }}
    >
      <DialogContent className="sm:max-w-5xl max-h-[90dvh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        {children}
      </DialogContent>
    </Dialog>
  );
}
export function Confirm({
  title,
  description,
  open,
  busy,
  error,
  onClose,
  onConfirm,
}: {
  title: string;
  description: string;
  open: boolean;
  busy: boolean;
  error: unknown;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <Modal
      title={title}
      description={description}
      open={open}
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      <ErrorMessage error={error} />
      <div className="actions justify-end">
        <Button variant="outline" disabled={busy} onClick={onClose}>
          Keep
        </Button>
        <Button variant="destructive" disabled={busy} onClick={onConfirm}>
          {busy ? "Working…" : "Confirm"}
        </Button>
      </div>
    </Modal>
  );
}
export function pretty(value: string) {
  try {
    return JSON.stringify(JSON.parse(value), null, 2);
  } catch {
    return value;
  }
}
export function safeURL(value: string) {
  try {
    const u = new URL(value);
    return ["https:", "http:"].includes(u.protocol) ? u.href : undefined;
  } catch {
    return undefined;
  }
}
export function duration(task: { started_at?: string; ended_at?: string }) {
  return task.started_at
    ? `${Math.max(0, Math.round(((task.ended_at ? Date.parse(task.ended_at) : Date.now()) - Date.parse(task.started_at)) / 1000))}s`
    : "—";
}
