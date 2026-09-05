import { useState } from "react";
import { useAPI, useAction, request } from "../lib/api";
import type { Target } from "../lib/types";
import { Button, ErrorMessage, Modal } from "./shared";
import { Input } from "./ui/input";

export default function ImportHAR({
  session,
  onClose,
}: {
  session: string;
  onClose: () => void;
}) {
  const targets = useAPI<Target[]>(`/sessions/${session}/targets`);
  const [target, setTarget] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [count, setCount] = useState<number | null>(null);
  const upload = useAction(async () => {
    if (!file || !target) throw new Error("Choose a target and HAR file.");
    const data = new FormData();
    data.append("har", file);
    const result = await request<{ imported: number }>(
      `/targets/${target}/transactions/import`,
      "POST",
      data,
    );
    setCount(result.imported);
    setFile(null);
  });
  return (
    <Modal
      open
      title="Import HAR"
      description="Attach captured HTTP transactions to a target. Importing does not replay requests."
      onClose={() => {
        if (!upload.isPending) onClose();
      }}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          upload.mutate(undefined);
        }}
      >
        <label>
          Target
          <select
            value={target}
            disabled={upload.isPending}
            required
            onChange={(e) => setTarget(e.target.value)}
          >
            <option value="">Select target</option>
            {targets.data?.map((t) => (
              <option key={t.id} value={t.id}>
                {t.value}
              </option>
            ))}
          </select>
        </label>
        <label>
          HAR file
          <Input
            type="file"
            accept=".har,application/json"
            disabled={upload.isPending}
            required
            onChange={(e) => {
              setFile(e.target.files?.[0] || null);
              setCount(null);
            }}
          />
        </label>
        <ErrorMessage error={targets.error || upload.error} />
        <Button type="submit" disabled={!file || !target || upload.isPending}>
          Import
        </Button>
        {count !== null && <p role="status">Imported {count} transactions.</p>}
        {upload.isError && (
          <p>
            Check transactions before submitting again if the response was lost.
            Imports are not retried automatically.
          </p>
        )}
      </form>
    </Modal>
  );
}
