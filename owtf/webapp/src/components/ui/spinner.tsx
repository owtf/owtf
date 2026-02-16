import * as React from "react";
import { Loader2 } from "lucide-react";
import { cn } from "../../lib/utils";

interface SpinnerProps {
  size?: number;
  className?: string;
}

export function Spinner({ size = 18, className }: SpinnerProps) {
  return (
    <Loader2
      className={cn("animate-spin text-zinc-500", className)}
      style={{ width: size, height: size }}
      aria-label="Loading"
    />
  );
}
