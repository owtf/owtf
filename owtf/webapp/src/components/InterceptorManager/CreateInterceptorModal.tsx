import React, { useState } from "react";

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
import { Textarea } from "../ui/textarea";
import { Interceptor, InterceptorType, CreateInterceptorRequest } from "./types";

interface CreateInterceptorModalProps {
  onClose: () => void;
  onCreated: (interceptor: Interceptor) => void;
}

const fieldWrapperClass = "space-y-2";
const sectionClass = "space-y-4 rounded-lg border border-zinc-200 bg-zinc-50 p-4";

const CreateInterceptorModal: React.FC<CreateInterceptorModalProps> = ({ onClose, onCreated }) => {
  const [type, setType] = useState<InterceptorType>("header");
  const [name, setName] = useState("");
  const [config, setConfig] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

      const request: CreateInterceptorRequest = {
        type,
        name: name.trim(),
        config,
      };

      const response = await fetch("/api/v1/interceptors/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      const newInterceptor: Interceptor = {
        id: result.id,
        name: name.trim(),
        type,
        enabled: true,
        priority: 100,
        config,
      };

      onCreated(newInterceptor);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create interceptor");
    } finally {
      setLoading(false);
    }
  };

  const renderConfigFields = () => {
    switch (type) {
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
          <DialogTitle>Create New Interceptor</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className={fieldWrapperClass}>
            <Label htmlFor="interceptor-name">Interceptor Name *</Label>
            <Input
              id="interceptor-name"
              placeholder="My Custom Interceptor"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className={fieldWrapperClass}>
            <Label htmlFor="interceptor-type">Interceptor Type</Label>
            <select
              id="interceptor-type"
              className="flex h-10 w-full rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm"
              value={type}
              onChange={(e) => {
                setType(e.target.value as InterceptorType);
                setConfig({});
              }}
            >
              <option value="header">Header Modifier</option>
              <option value="body">Body Modifier</option>
              <option value="url">URL Rewriter</option>
              <option value="delay">Delay Injector</option>
            </select>
          </div>

          {renderConfigFields()}

          {error && (
            <Alert variant="danger">
              <AlertTitle>Create failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button type="button" onClick={handleSubmit} disabled={loading || !name.trim()}>
            {loading ? "Creating..." : "Create Interceptor"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CreateInterceptorModal;
