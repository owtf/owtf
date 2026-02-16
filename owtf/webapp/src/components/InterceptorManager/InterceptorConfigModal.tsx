import React, { useEffect, useState } from "react";

import { Alert, AlertDescription, AlertTitle } from "../ui/alert";
import { Button } from "../ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Switch } from "../ui/switch";
import { Textarea } from "../ui/textarea";
import { Interceptor, UpdateInterceptorRequest } from "./types";

interface InterceptorConfigModalProps {
  interceptor: Interceptor;
  onClose: () => void;
  onSave: (interceptor: Interceptor) => void;
}

const fieldWrapperClass = "space-y-2";
const sectionClass = "space-y-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4";

const InterceptorConfigModal: React.FC<InterceptorConfigModalProps> = ({
  interceptor,
  onClose,
  onSave,
}) => {
  const [name, setName] = useState(interceptor.name);
  const [enabled, setEnabled] = useState(interceptor.enabled);
  const [priority, setPriority] = useState(interceptor.priority);
  const [config, setConfig] = useState<Record<string, any>>(interceptor.config);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setName(interceptor.name);
    setEnabled(interceptor.enabled);
    setPriority(interceptor.priority);
    setConfig(interceptor.config);
  }, [interceptor]);

  const parseJsonAndSet = (value: string, key: string) => {
    try {
      const parsed = JSON.parse(value);
      setConfig((prev) => ({ ...prev, [key]: parsed }));
    } catch {
      // Keep typing behavior permissive for partial JSON entry.
    }
  };

  const handleSubmit = async () => {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const request: UpdateInterceptorRequest = {
        enabled,
        priority,
        config,
      };

      const response = await fetch(`/api/v1/interceptors/${interceptor.id}/config/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const updatedInterceptor: Interceptor = {
        ...interceptor,
        name: name.trim(),
        enabled,
        priority,
        config,
      };

      onSave(updatedInterceptor);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update interceptor");
    } finally {
      setLoading(false);
    }
  };

  const renderConfigFields = () => {
    switch (interceptor.type) {
      case "header":
        return (
          <div className={sectionClass}>
            <div className={fieldWrapperClass}>
              <Label htmlFor="headers-to-add">Headers to Add (JSON format)</Label>
              <Textarea
                id="headers-to-add"
                placeholder='{"X-Custom-Header":"value","Authorization":"Bearer token"}'
                value={config.headers_to_add ? JSON.stringify(config.headers_to_add, null, 2) : ""}
                onChange={(e) => parseJsonAndSet(e.target.value, "headers_to_add")}
                rows={4}
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="headers-to-remove">Headers to Remove (comma-separated)</Label>
              <Input
                id="headers-to-remove"
                placeholder="Server, X-Powered-By, X-AspNet-Version"
                value={Array.isArray(config.headers_to_remove) ? config.headers_to_remove.join(", ") : ""}
                onChange={(e) => {
                  const headers = e.target.value.split(",").map((h) => h.trim()).filter(Boolean);
                  setConfig((prev) => ({ ...prev, headers_to_remove: headers }));
                }}
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="headers-to-modify">Headers to Modify (JSON format)</Label>
              <Textarea
                id="headers-to-modify"
                placeholder='{"User-Agent":"Custom User Agent","Accept":"application/json"}'
                value={config.headers_to_modify ? JSON.stringify(config.headers_to_modify, null, 2) : ""}
                onChange={(e) => parseJsonAndSet(e.target.value, "headers_to_modify")}
                rows={4}
              />
            </div>
          </div>
        );

      case "body":
        return (
          <div className={sectionClass}>
            <div className={fieldWrapperClass}>
              <Label htmlFor="search-replace">Search and Replace Patterns (JSON format)</Label>
              <Textarea
                id="search-replace"
                placeholder='{"old text":"new text","pattern":"replacement"}'
                value={config.search_replace ? JSON.stringify(config.search_replace, null, 2) : ""}
                onChange={(e) => parseJsonAndSet(e.target.value, "search_replace")}
                rows={4}
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="body-prepend">Text to Prepend</Label>
              <Input
                id="body-prepend"
                placeholder="<!-- Modified by OWTF -->"
                value={config.body_prepend || ""}
                onChange={(e) => setConfig((prev) => ({ ...prev, body_prepend: e.target.value }))}
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="body-append">Text to Append</Label>
              <Input
                id="body-append"
                placeholder="<!-- End of modification -->"
                value={config.body_append || ""}
                onChange={(e) => setConfig((prev) => ({ ...prev, body_append: e.target.value }))}
              />
            </div>
          </div>
        );

      case "url":
        return (
          <div className={sectionClass}>
            <div className={fieldWrapperClass}>
              <Label htmlFor="url-patterns">URL Patterns (JSON format)</Label>
              <Textarea
                id="url-patterns"
                placeholder='{"old\\.domain\\.com":"new.domain.com","api\\.v1":"api.v2"}'
                value={config.url_patterns ? JSON.stringify(config.url_patterns, null, 2) : ""}
                onChange={(e) => parseJsonAndSet(e.target.value, "url_patterns")}
                rows={4}
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="query-params">Query Parameter Modifications (JSON format)</Label>
              <Textarea
                id="query-params"
                placeholder='{"debug":"true","version":"2.0"}'
                value={config.query_param_modifications ? JSON.stringify(config.query_param_modifications, null, 2) : ""}
                onChange={(e) => parseJsonAndSet(e.target.value, "query_param_modifications")}
                rows={4}
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="path-modifications">Path Modifications (JSON format)</Label>
              <Textarea
                id="path-modifications"
                placeholder='{"/api/v1":"/api/v2","/old":"/new"}'
                value={config.path_modifications ? JSON.stringify(config.path_modifications, null, 2) : ""}
                onChange={(e) => parseJsonAndSet(e.target.value, "path_modifications")}
                rows={4}
              />
            </div>
          </div>
        );

      case "delay":
        return (
          <div className={sectionClass}>
            <div className={fieldWrapperClass}>
              <Label htmlFor="request-delay">Request Delay (seconds)</Label>
              <Input
                id="request-delay"
                type="number"
                step="0.1"
                min="0"
                placeholder="1.0"
                value={config.request_delay || ""}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, request_delay: parseFloat(e.target.value) || 0 }))
                }
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="response-delay">Response Delay (seconds)</Label>
              <Input
                id="response-delay"
                type="number"
                step="0.1"
                min="0"
                placeholder="0.5"
                value={config.response_delay || ""}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, response_delay: parseFloat(e.target.value) || 0 }))
                }
              />
            </div>
            <div className={fieldWrapperClass}>
              <Label htmlFor="jitter">Enable Jitter</Label>
              <select
                id="jitter"
                className="flex h-10 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm"
                value={config.jitter ? "true" : "false"}
                onChange={(e) => setConfig((prev) => ({ ...prev, jitter: e.target.value === "true" }))}
              >
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Interceptor: {interceptor.name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className={sectionClass}>
            <div className={fieldWrapperClass}>
              <Label htmlFor="interceptor-name">Interceptor Name *</Label>
              <Input
                id="interceptor-name"
                placeholder="My Custom Interceptor"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="flex items-center gap-2">
              <Switch
                id="interceptor-enabled"
                checked={enabled}
                onCheckedChange={(checked: boolean) => setEnabled(checked)}
              />
              <Label htmlFor="interceptor-enabled">Enable Interceptor</Label>
            </div>

            <div className={fieldWrapperClass}>
              <Label htmlFor="interceptor-priority">Priority (lower numbers = higher priority)</Label>
              <Input
                id="interceptor-priority"
                type="number"
                min="1"
                max="100"
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value, 10) || 100)}
              />
            </div>
          </div>

          {renderConfigFields()}

          {error && (
            <Alert variant="danger">
              <AlertTitle>Update failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="button" onClick={handleSubmit} disabled={loading || !name.trim()}>
            {loading ? "Saving..." : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default InterceptorConfigModal;
