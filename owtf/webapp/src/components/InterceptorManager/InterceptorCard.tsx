import React from "react";
import { Pencil, Trash2 } from "lucide-react";

import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Switch } from "../ui/switch";
import { Interceptor, InterceptorType } from "./types";

interface InterceptorCardProps {
  interceptor: Interceptor;
  onToggle: (enabled: boolean) => void;
  onEdit: () => void;
  onDelete: () => void;
  getStatusColor: (enabled: boolean) => string;
  getTypeColor: (type: InterceptorType) => string;
}

const statusClassMap: Record<string, string> = {
  success: "bg-emerald-100 text-emerald-800 border-emerald-200",
  danger: "bg-red-100 text-red-800 border-red-200",
};

const typeClassMap: Record<string, string> = {
  blue: "bg-zinc-100 text-zinc-800 border-zinc-200",
  green: "bg-emerald-100 text-emerald-800 border-emerald-200",
  orange: "bg-amber-100 text-amber-800 border-amber-200",
  purple: "bg-zinc-100 text-zinc-800 border-zinc-200",
  neutral: "bg-zinc-100 text-zinc-700 border-zinc-200",
};

const priorityClassMap = {
  Critical: "bg-red-100 text-red-800 border-red-200",
  High: "bg-orange-100 text-orange-800 border-orange-200",
  Medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  Low: "bg-zinc-100 text-zinc-800 border-zinc-200",
  "Very Low": "bg-zinc-100 text-zinc-700 border-zinc-200",
};

const InterceptorCard: React.FC<InterceptorCardProps> = ({
  interceptor,
  onToggle,
  onEdit,
  onDelete,
  getStatusColor,
  getTypeColor,
}) => {
  const getTypeLabel = (type: InterceptorType) => {
    const labels: Record<InterceptorType, string> = {
      header: "Header Modifier",
      body: "Body Modifier",
      url: "URL Rewriter",
      delay: "Delay Injector",
    };
    return labels[type] || type;
  };

  const getConfigSummary = () => {
    const { type, config } = interceptor;

    switch (type) {
      case "header": {
        const headerConfig = config as any;
        const addCount = Object.keys(headerConfig.headers_to_add || {}).length;
        const removeCount = (headerConfig.headers_to_remove || []).length;
        const modifyCount = Object.keys(headerConfig.headers_to_modify || {}).length;
        return `${addCount} add, ${removeCount} remove, ${modifyCount} modify`;
      }
      case "body": {
        const bodyConfig = config as any;
        const searchCount = Object.keys(bodyConfig.search_replace || {}).length;
        const hasPrepend = bodyConfig.body_prepend ? 1 : 0;
        const hasAppend = bodyConfig.body_append ? 1 : 0;
        return `${searchCount} patterns, ${hasPrepend + hasAppend} injections`;
      }
      case "url": {
        const urlConfig = config as any;
        const patternCount = Object.keys(urlConfig.url_patterns || {}).length;
        const paramCount = Object.keys(urlConfig.query_param_modifications || {}).length;
        const pathCount = Object.keys(urlConfig.path_modifications || {}).length;
        return `${patternCount} patterns, ${paramCount} params, ${pathCount} paths`;
      }
      case "delay": {
        const delayConfig = config as any;
        const requestDelay = delayConfig.request_delay || 0;
        const responseDelay = delayConfig.response_delay || 0;
        const hasJitter = delayConfig.jitter ? "with jitter" : "no jitter";
        return `${requestDelay}s req, ${responseDelay}s resp, ${hasJitter}`;
      }
      default:
        return "No configuration";
    }
  };

  const getPriorityLabel = (priority: number) => {
    if (priority <= 20) return "Critical";
    if (priority <= 40) return "High";
    if (priority <= 60) return "Medium";
    if (priority <= 80) return "Low";
    return "Very Low";
  };

  const priorityLabel = getPriorityLabel(interceptor.priority);
  const typeClass = typeClassMap[getTypeColor(interceptor.type)] || typeClassMap.neutral;
  const statusClass = statusClassMap[getStatusColor(interceptor.enabled)] || statusClassMap.danger;

  return (
    <Card className="h-full border-zinc-200 bg-white/95 shadow-sm transition-shadow hover:shadow-md">
      <CardHeader className="space-y-3 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <CardTitle className="text-base font-semibold tracking-tight text-zinc-900">
              {interceptor.name}
            </CardTitle>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className={typeClass}>{getTypeLabel(interceptor.type)}</Badge>
              <Badge className={priorityClassMap[priorityLabel]}>
                {priorityLabel} ({interceptor.priority})
              </Badge>
            </div>
          </div>
          <Switch
            checked={interceptor.enabled}
            onCheckedChange={(checked: boolean) => onToggle(checked)}
            aria-label={`Toggle interceptor ${interceptor.name}`}
          />
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pt-0">
        <p className="text-sm text-zinc-600">{getConfigSummary()}</p>
        <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm">
          <span>
            Status:{" "}
            <Badge className={statusClass}>
              {interceptor.enabled ? "Active" : "Inactive"}
            </Badge>
          </span>
          <span className="text-xs text-zinc-500">ID: {interceptor.id}</span>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onEdit}>
            <Pencil className="h-3.5 w-3.5" />
            Edit
          </Button>
          <Button variant="destructive" size="sm" onClick={onDelete}>
            <Trash2 className="h-3.5 w-3.5" />
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default InterceptorCard;
