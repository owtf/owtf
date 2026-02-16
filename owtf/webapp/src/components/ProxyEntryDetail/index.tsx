/**
 * ProxyEntryDetail
 *
 * Component to display detailed information about a proxy entry
 */

import React from "react";

import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

interface ProxyEntryDetailProps {
  entry: any;
  onClose: () => void;
}

const ProxyEntryDetail: React.FC<ProxyEntryDetailProps> = ({ entry, onClose }) => {
  const formatHeaders = (headers: any) => {
    if (!headers || typeof headers !== "object") return "No headers";

    return Object.entries(headers)
      .map(([key, value]) => `${key}: ${value}`)
      .join("\n");
  };

  const formatBody = (body: any) => {
    if (!body) return "No body content";

    if (typeof body === "string") {
      try {
        const parsed = JSON.parse(body);
        return JSON.stringify(parsed, null, 2);
      } catch {
        return body;
      }
    }

    return String(body);
  };

  const formatRaw = (data: any) => {
    const lines = [];

    if (data.direction === "REQUEST") {
      lines.push(`${data.method} ${data.url} HTTP/1.1`);
    } else {
      lines.push(`HTTP/1.1 ${data.status_code} Response`);
    }

    if (data.headers && typeof data.headers === "object") {
      Object.entries(data.headers).forEach(([key, value]) => {
        lines.push(`${key}: ${value}`);
      });
    }

    lines.push("");

    if (data.body) {
      lines.push(formatBody(data.body));
    }

    return lines.join("\n");
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85vh] max-w-5xl overflow-hidden p-0">
        <DialogHeader className="border-b border-slate-200 px-6 py-4">
          <DialogTitle className="truncate text-base">
            {entry.direction} - {entry.method} {entry.url}
          </DialogTitle>
        </DialogHeader>

        <div className="flex h-[70vh] flex-col overflow-hidden p-4">
          <Tabs defaultValue="headers" className="flex h-full flex-col overflow-hidden">
            <TabsList className="w-fit">
              <TabsTrigger value="headers">Headers</TabsTrigger>
              <TabsTrigger value="body">Body</TabsTrigger>
              <TabsTrigger value="raw">Raw</TabsTrigger>
            </TabsList>

            <TabsContent value="headers" className="mt-3 flex-1 overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-800">Headers</h4>
              <pre className="whitespace-pre-wrap text-xs text-slate-700">{formatHeaders(entry.headers)}</pre>
            </TabsContent>

            <TabsContent value="body" className="mt-3 flex-1 overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-800">Body</h4>
              <pre className="whitespace-pre-wrap text-xs text-slate-700">{formatBody(entry.body)}</pre>
            </TabsContent>

            <TabsContent value="raw" className="mt-3 flex-1 overflow-auto rounded-lg border border-slate-200 bg-slate-50 p-4">
              <h4 className="mb-2 text-sm font-semibold text-slate-800">Raw</h4>
              <pre className="whitespace-pre-wrap text-xs text-slate-700">{formatRaw(entry)}</pre>
            </TabsContent>
          </Tabs>
        </div>

        <div className="flex items-end justify-between gap-4 border-t border-slate-200 bg-white px-6 py-4">
          <div className="space-y-1 text-xs text-slate-600">
            <div><strong>Timestamp:</strong> {entry.timestamp}</div>
            <div><strong>Protocol:</strong> {entry.protocol}</div>
            <div><strong>Direction:</strong> {entry.direction}</div>
            {entry.body_size && (
              <div><strong>Body Size:</strong> {entry.body_size} bytes</div>
            )}
          </div>
          <Button
            type="button"
            onClick={() => {
              sessionStorage.setItem("owtf_repeater_pending_entry", JSON.stringify(entry));
              onClose();
              alert("Request sent to Repeater! Switch to the Repeater tab to view and edit it.");
            }}
            title="Send this request to the Repeater tab"
          >
            Send to Repeater
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProxyEntryDetail;
